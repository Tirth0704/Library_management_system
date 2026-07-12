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
                               return_date: date = None) -> Fine:
    """
    Core function called during return processing.

    Creates a single consolidated Fine record based on return conditions:
        - If Lost: lost fine (full book price)
        - Else: rent fine (standard rent + late fine if overdue + damage fine if damaged)

    Args:
        issue:              The BookIssue record being returned
        condition:          'Good' | 'Damaged' | 'Lost'
        damage_fine_amount: Variable amount set by librarian (only for Damaged)
        return_date:        Date of return (defaults to today)

    Returns:
        A single Fine object (added to db session, not yet committed).
    """
    if return_date is None:
        return_date = date.today()

    book = Book.query.get(issue.book_id)

    if condition == "Lost":
        lost_amount = calculate_lost_amount(book.price)
        fine = Fine(
            student_id=issue.student_id,
            issue_id=issue.id,
            fine_type="lost",
            amount=lost_amount,
            description=f"Lost book: {book.title}"
        )
    else:
        rent_amount = calculate_rent(book.price)
        late_amount = Decimal("0.00")
        
        overdue_days = (return_date - issue.due_date).days
        if overdue_days > 0:
            late_amount = calculate_late_fine(book.price, overdue_days)
            
        damage_amount = Decimal("0.00")
        if condition == "Damaged":
            damage_amount = damage_fine_amount

        total_amount = rent_amount + late_amount + damage_amount

        # Build description breakdown
        details = []
        if late_amount > 0:
            details.append(f"₹{late_amount:.2f} late return fine")
        if damage_amount > 0:
            details.append(f"₹{damage_amount:.2f} damage fine")
            
        if details:
            desc = f"Rent for: {book.title} (includes {', '.join(details)})"
        else:
            desc = f"Rent for: {book.title}"

        fine = Fine(
            student_id=issue.student_id,
            issue_id=issue.id,
            fine_type="rent",
            amount=total_amount,
            description=desc
        )

    db.session.add(fine)
    return fine


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