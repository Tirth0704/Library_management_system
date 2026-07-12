from datetime import date
from decimal import Decimal
from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models.issue import BookIssue
from app.models.return_ import BookReturn
from app.models.book import Book
from app.models.student import Student
from app.models.activity_log import ActivityLog
from app.forms.return_forms import ProcessReturnForm
from app.utils.decorators import librarian_required
from app.services.fine_service import generate_fines_for_return
from app.services.behaviour_service import (
    record_returned_on_time,
    record_returned_early,
    record_returned_late,
    record_lost_book,
    record_damaged_book,
    record_damage_fine_added
)

librarian_returns_bp = Blueprint("librarian_returns", __name__,
                                  url_prefix="/librarian")


@librarian_returns_bp.route("/returns")
@librarian_required
def return_list():
    """Lists active issues that can be processed for return."""
    issues = BookIssue.query.filter_by(
        is_returned=False,
        is_lost=False
    ).order_by(BookIssue.due_date.asc()).all()

    return render_template(
        "librarian/returns/process.html",
        issues=issues,
        today=date.today(),
        title="Process Returns"
    )


@librarian_returns_bp.route("/returns/<int:issue_id>")
@librarian_required
def return_detail(issue_id: int):
    """Shows the return form for a specific issue."""
    issue = BookIssue.query.get_or_404(issue_id)

    if issue.is_returned or issue.is_lost:
        flash("This book has already been returned or marked lost.", "warning")
        return redirect(url_for("librarian_returns.return_list"))

    book = Book.query.get(issue.book_id)
    student = Student.query.get(issue.student_id)
    form = ProcessReturnForm()

    today = date.today()
    overdue_days = max(0, (today - issue.due_date).days)
    is_early = today < issue.due_date

    return render_template(
        "librarian/returns/process.html",
        issue=issue,
        book=book,
        student=student,
        form=form,
        today=today,
        overdue_days=overdue_days,
        is_early=is_early,
        title=f"Return: {book.title}"
    )


@librarian_returns_bp.route("/returns/<int:issue_id>/complete", methods=["POST"])
@librarian_required
def complete_return(issue_id: int):
    """
    Processes the complete return of a book.

    Steps:
    1. Validate form and issue state
    2. Determine return condition (Good / Damaged / Lost)
    3. Calculate and create fine records
    4. Update BookIssue (mark returned/lost)
    5. Update BookReturn record
    6. Update book inventory (return_copy)
    7. Update behaviour score
    8. Log activity
    """
    issue = BookIssue.query.get_or_404(issue_id)

    if issue.is_returned or issue.is_lost:
        flash("Already processed.", "warning")
        return redirect(url_for("librarian_returns.return_list"))

    form = ProcessReturnForm()

    if not form.validate_on_submit():
        flash("Invalid form submission.", "danger")
        return redirect(url_for("librarian_returns.return_detail",
                                issue_id=issue_id))

    book = Book.query.get(issue.book_id)
    student = Student.query.get(issue.student_id)
    today = date.today()
    condition = form.condition.data
    damage_fine_amount = Decimal(str(form.damage_fine.data or 0))

    # ── Generate Fines ─────────────────────────────────────────────────────────
    fines = generate_fines_for_return(
        issue=issue,
        condition=condition,
        damage_fine_amount=damage_fine_amount,
        return_date=today
    )

    # ── Update BookIssue ───────────────────────────────────────────────────────
    if condition == "Lost":
        issue.is_lost = True
        issue.status = "Lost"
    else:
        issue.is_returned = True
        issue.return_date = today
        issue.status = "Returned"

    # ── Update Book Inventory ──────────────────────────────────────────────────
    book.return_copy()

    # ── Create BookReturn Record ───────────────────────────────────────────────
    rent_amount = next(
        (f.amount for f in fines if f.fine_type == "rent"), Decimal("0.00")
    )
    late_fine = next(
        (f.amount for f in fines if f.fine_type == "late"), Decimal("0.00")
    )
    damage_fine_recorded = next(
        (f.amount for f in fines if f.fine_type == "damage"), Decimal("0.00")
    )
    lost_amount = next(
        (f.amount for f in fines if f.fine_type == "lost"), Decimal("0.00")
    )
    total_due = sum(f.amount for f in fines)

    book_return = BookReturn(
        issue_id=issue.id,
        student_id=student.id,
        book_id=book.id,
        return_date=today,
        condition=condition,
        rent_charged=rent_amount,
        late_fine=late_fine,
        damage_fine=damage_fine_recorded,
        lost_amount=lost_amount,
        total_due=total_due,
        librarian_notes=form.librarian_notes.data
    )
    db.session.add(book_return)

    # ── Behaviour Score ────────────────────────────────────────────────────────
    if condition == "Lost":
        record_lost_book(student, book.title)
    elif condition == "Damaged":
        record_damaged_book(student, book.title)
        if damage_fine_amount > Decimal("0.00"):
            record_damage_fine_added(student, book.title)
    else:
        overdue_days = max(0, (today - issue.due_date).days)
        if today < issue.due_date:
            record_returned_early(student, book.title)
        elif overdue_days == 0:
            record_returned_on_time(student, book.title)
        else:
            record_returned_late(student, book.title)

    # ── Activity Log ───────────────────────────────────────────────────────────
    log = ActivityLog(
        actor_type="librarian",
        entity_type="book_return",
        entity_id=book_return.id,
        action="return_processed",
        description=(
            f"Return processed for '{book.title}' "
            f"by {student.full_name}. "
            f"Condition: {condition}. Total Due: ₹{float(total_due):.2f}"
        )
    )
    db.session.add(log)
    db.session.commit()

    # ── WhatsApp Notification ──────────────────────────────────────────────────
    try:
        from flask import current_app
        from app.services.whatsapp_service import send_book_returned
        send_book_returned(student, book.title, condition, float(total_due))
    except Exception as e:
        try:
            current_app.logger.error(f"Failed to send return WhatsApp notification: {e}")
        except Exception:
            print(f"Failed to send return WhatsApp notification: {e}")

    flash(
        f"Return processed. Total amount due: ₹{float(total_due):.2f}.",
        "success"
    )
    return redirect(url_for("librarian_returns.return_list"))
