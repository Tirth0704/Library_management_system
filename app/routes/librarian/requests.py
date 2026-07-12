from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.request import BookRequest
from app.models.issue import BookIssue
from app.models.book import Book
from app.models.student import Student
from app.models.activity_log import ActivityLog
from app.forms.request_forms import ApproveRequestForm, RejectRequestForm
from app.utils.decorators import librarian_required
from app.services.notification_service import (
    notify_request_approved,
    notify_request_rejected
)
from app.services.whatsapp_service import (
    send_request_approved,
    send_request_rejected
)
from config import ActiveConfig

librarian_requests_bp = Blueprint(
    "librarian_requests",
    __name__,
    url_prefix="/librarian"
)


@librarian_requests_bp.route("/requests")
@librarian_required
def request_list():
    """
    Lists all book requests filtered by status.
    Default filter is 'Pending'.

    Status options: Pending / Approved / Rejected / Hold / Cancelled
    """
    status_filter = request.args.get("status", "Pending")

    requests = BookRequest.query.filter_by(
        status=status_filter
    ).order_by(BookRequest.requested_at.desc()).all()

    return render_template(
        "librarian/requests/list.html",
        requests=requests,
        status_filter=status_filter,
        today=date.today(),
        title="Book Requests"
    )


@librarian_requests_bp.route(
    "/requests/<int:request_id>/approve",
    methods=["POST"]
)
@librarian_required
def approve_request(request_id: int):
    """
    Approves a book request.

    Steps:
    1. Validate request is Pending
    2. Validate book has available copies
    3. Create BookIssue record with due_date = issue_date + 14 days
    4. Decrement book available_copies (via issue_copy())
    5. Update request status to Approved
    6. Send WhatsApp + in-app notification
    7. Log activity
    """
    book_request = BookRequest.query.get_or_404(request_id)
    form = ApproveRequestForm()

    if book_request.status != "Pending":
        flash("This request is no longer pending.", "warning")
        return redirect(url_for("librarian_requests.request_list"))

    book = Book.query.get(book_request.book_id)
    student = Student.query.get(book_request.student_id)

    if not book or book.available_copies < 1:
        flash("Book is unavailable. Cannot approve.", "danger")
        return redirect(url_for("librarian_requests.request_list"))

    if form.validate_on_submit():
        issue_date = form.issue_date.data
        due_date = issue_date + timedelta(days=ActiveConfig.LOAN_PERIOD_DAYS)

        # Create issue record
        issue = BookIssue(
            student_id=student.id,
            book_id=book.id,
            request_id=book_request.id,
            issue_date=issue_date,
            due_date=due_date,
            is_returned=False,
            is_lost=False,
            status="Issued"
        )
        db.session.add(issue)

        # Decrement book copy inventory
        book.issue_copy()

        # Update request status
        book_request.status = "Approved"

        # Flush to get issue.id for the activity log
        db.session.flush()

        # Activity log
        log = ActivityLog(
            actor_type="librarian",
            entity_type="book_issue",
            entity_id=issue.id,
            action="request_approved",
            description=(
                f"Approved request for '{book.title}' "
                f"by {student.full_name}. Due: {due_date}"
            )
        )
        db.session.add(log)
        db.session.commit()

        # Send in-app notification
        notify_request_approved(student.id, book.title, due_date)
        db.session.commit()

        # Send WhatsApp notification (never crash on Twilio failure)
        try:
            send_request_approved(student, book.title, due_date)
        except Exception as e:
            from flask import current_app as _app
            _app.logger.error(f"WhatsApp approve notification failed: {e}")

        flash(
            f"Request approved. '{book.title}' issued to {student.full_name}.",
            "success"
        )
    else:
        flash("Invalid form submission. Please provide a valid issue date.", "danger")

    return redirect(url_for("librarian_requests.request_list"))


@librarian_requests_bp.route(
    "/requests/<int:request_id>/reject",
    methods=["POST"]
)
@librarian_required
def reject_request(request_id: int):
    """
    Rejects a book request with a mandatory reason.
    Records rejected_at timestamp for 24-hour re-request enforcement.
    """
    book_request = BookRequest.query.get_or_404(request_id)
    form = RejectRequestForm()

    if book_request.status != "Pending":
        flash("This request is no longer pending.", "warning")
        return redirect(url_for("librarian_requests.request_list"))

    if form.validate_on_submit():
        book = Book.query.get(book_request.book_id)
        student = Student.query.get(book_request.student_id)

        book_request.status = "Rejected"
        book_request.rejection_reason = form.rejection_reason.data.strip()
        book_request.rejected_at = datetime.utcnow()

        log = ActivityLog(
            actor_type="librarian",
            entity_type="book_request",
            entity_id=book_request.id,
            action="request_rejected",
            description=(
                f"Rejected request for '{book.title}' "
                f"by {student.full_name}. "
                f"Reason: {book_request.rejection_reason}"
            )
        )
        db.session.add(log)
        db.session.commit()

        # Send in-app notification
        notify_request_rejected(
            student.id, book.title, book_request.rejection_reason
        )
        db.session.commit()

        # Send WhatsApp notification (never crash on Twilio failure)
        try:
            send_request_rejected(
                student, book.title, book_request.rejection_reason
            )
        except Exception as e:
            from flask import current_app as _app
            _app.logger.error(f"WhatsApp reject notification failed: {e}")

        flash(f"Request for '{book.title}' rejected.", "info")
    else:
        flash("Please provide a rejection reason.", "danger")

    return redirect(url_for("librarian_requests.request_list"))


@librarian_requests_bp.route(
    "/requests/<int:request_id>/hold",
    methods=["POST"]
)
@librarian_required
def hold_request(request_id: int):
    """
    Manually places a request on hold.
    Typically used when student has unpaid fines that need clearing.
    """
    book_request = BookRequest.query.get_or_404(request_id)

    if book_request.status == "Pending":
        book_request.status = "Hold"

        log = ActivityLog(
            actor_type="librarian",
            entity_type="book_request",
            entity_id=book_request.id,
            action="request_held",
            description=(
                f"Request placed on hold for book ID {book_request.book_id}."
            )
        )
        db.session.add(log)
        db.session.commit()

        flash("Request placed on hold.", "info")
    else:
        flash("Cannot place this request on hold.", "warning")

    return redirect(url_for("librarian_requests.request_list"))