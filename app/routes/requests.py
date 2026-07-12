from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.models.request import BookRequest
from app.models.issue import BookIssue
from app.models.book import Book
from app.models.activity_log import ActivityLog
from app.utils.decorators import student_required
from app.services.notification_service import get_unread_count
from app.services.behaviour_service import record_cancelled_approved

requests_bp = Blueprint("requests", __name__)


@requests_bp.route("/my-requests")
@student_required
def my_requests():
    """Student view of all their book requests with current status."""
    student = current_user

    requests = BookRequest.query.filter_by(
        student_id=student.id
    ).order_by(BookRequest.requested_at.desc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/my_requests.html",
        requests=requests,
        unread_count=unread_count,
        title="My Requests"
    )


@requests_bp.route("/requests/<int:request_id>/cancel", methods=["POST"])
@student_required
def cancel_request(request_id: int):
    """
    Student can cancel a request.

    - PENDING request → simple cancel, no penalty.
    - APPROVED request → behaviour score -3 (as per spec:
      'Cancelled approved request').
    - Any other status → cannot be cancelled.
    """
    student = current_user
    req = BookRequest.query.filter_by(
        id=request_id,
        student_id=student.id
    ).first_or_404()

    if req.status == "Pending":
        req.status = "Cancelled"
        db.session.flush()

        log = ActivityLog(
            actor_type="student",
            actor_id=student.id,
            entity_type="book_request",
            entity_id=req.id,
            action="cancelled_request",
            description=f"Student cancelled pending request for book ID {req.book_id}."
        )
        db.session.add(log)
        db.session.commit()

        flash("Request cancelled successfully.", "info")

    elif req.status == "Approved":
        # Cancelling an approved request → behaviour penalty
        book = Book.query.get(req.book_id)
        book_title = book.title if book else f"Book #{req.book_id}"

        req.status = "Cancelled"

        # Apply -3 behaviour score
        record_cancelled_approved(student, book_title)

        db.session.flush()

        log = ActivityLog(
            actor_type="student",
            actor_id=student.id,
            entity_type="book_request",
            entity_id=req.id,
            action="cancelled_approved_request",
            description=(
                f"Student cancelled APPROVED request for '{book_title}'. "
                f"Behaviour score penalty applied."
            )
        )
        db.session.add(log)
        db.session.commit()

        flash(
            "Approved request cancelled. Your behaviour score has been reduced by 3.",
            "warning"
        )

    else:
        flash("This request cannot be cancelled.", "warning")

    return redirect(url_for("requests.my_requests"))


@requests_bp.route("/my-books")
@student_required
def my_books():
    """Shows currently issued (active) books for the student."""
    student = current_user

    active_issues = BookIssue.query.filter_by(
        student_id=student.id,
        is_returned=False,
        is_lost=False
    ).order_by(BookIssue.due_date.asc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/my_books.html",
        issues=active_issues,
        unread_count=unread_count,
        today=date.today(),
        title="My Books"
    )


@requests_bp.route("/my-history")
@student_required
def my_history():
    """Shows student's full borrowing history (returned + lost)."""
    student = current_user

    past_issues = BookIssue.query.filter(
        BookIssue.student_id == student.id,
        db.or_(
            BookIssue.is_returned == True,
            BookIssue.is_lost == True
        )
    ).order_by(BookIssue.created_at.desc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/my_history.html",
        issues=past_issues,
        unread_count=unread_count,
        title="My History"
    )