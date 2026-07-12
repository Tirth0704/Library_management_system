from decimal import Decimal
from datetime import date
from app import db
from app.models.fine import Fine
from app.models.issue import BookIssue
from app.models.book import Book
from app.utils.helpers import (
    calculate_rent,
    calculate_late_fine,
    calculate_lost_amount,
)


def generate_fines_for_return(issue: BookIssue, condition: str,
                               damage_fine_amount: Decimal = Decimal("0.00"),
                               return_date: date = None) -> list[Fine]:
    """
    Core function called during return processing.

    Creates Fine records based on return conditions:
        - Always creates rent fine (unless lost)
        - Creates late fine if overdue at return date
        - Creates damage fine if condition == 'Damaged'
        - Creates lost fine if condition == 'Lost' (full book price)

    Args:
        issue:              The BookIssue record being returned
        condition:          'Good' | 'Damaged' | 'Lost'
        damage_fine_amount: Variable amount set by librarian (only for Damaged)
        return_date:        Date of return (defaults to today)

    Returns:
        List of Fine objects (not yet committed — caller commits).
    """
    if return_date is None:
        return_date = date.today()

    book = Book.query.get(issue.book_id)
    fines_created = []

    if condition == "Lost":
        # Lost → full book price only, no rent, no late fine
        lost_fine = Fine(
            student_id=issue.student_id,
            issue_id=issue.id,
            fine_type="lost",
            amount=calculate_lost_amount(book.price),
            description=f"Lost book: {book.title}"
        )
        db.session.add(lost_fine)
        fines_created.append(lost_fine)

    else:
        # Rent — always charged on return (not for lost)
        rent_amount = calculate_rent(book.price)
        rent_fine = Fine(
            student_id=issue.student_id,
            issue_id=issue.id,
            fine_type="rent",
            amount=rent_amount,
            description=f"Rent for: {book.title}"
        )
        db.session.add(rent_fine)
        fines_created.append(rent_fine)

        # Late fine — only if returned after due date
        overdue_days = (return_date - issue.due_date).days
        if overdue_days > 0:
            late_amount = calculate_late_fine(book.price, overdue_days)
            late_fine = Fine(
                student_id=issue.student_id,
                issue_id=issue.id,
                fine_type="late",
                amount=late_amount,
                description=(
                    f"Late return: {overdue_days} day(s) overdue for {book.title}"
                )
            )
            db.session.add(late_fine)
            fines_created.append(late_fine)

        # Damage fine — variable, set by librarian
        if condition == "Damaged" and damage_fine_amount > Decimal("0.00"):
            damage_fine = Fine(
                student_id=issue.student_id,
                issue_id=issue.id,
                fine_type="damage",
                amount=damage_fine_amount,
                description=f"Damage fine for: {book.title}"
            )
            db.session.add(damage_fine)
            fines_created.append(damage_fine)

    return fines_created


def get_unpaid_fines(student_id: int) -> list[Fine]:
    """Returns all unpaid fines for a student."""
    return Fine.query.filter_by(
        student_id=student_id,
        status="Unpaid"
    ).all()


def get_total_unpaid_amount(student_id: int) -> Decimal:
    """Returns total unpaid fine amount for a student."""
    fines = get_unpaid_fines(student_id)
    return sum((f.amount for f in fines), Decimal("0.00"))


def mark_fine_paid(fine: Fine, paid_at=None) -> None:
    """
    Marks a single fine as paid.
    Sets paid_at timestamp.
    Caller must commit.
    """
    from datetime import datetime
    fine.status = "Paid"
    fine.paid_at = paid_at or datetime.utcnow()