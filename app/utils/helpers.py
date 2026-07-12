from datetime import date
from decimal import Decimal
from config import ActiveConfig


def calculate_rent(book_price) -> Decimal:
    """
    Rent = 10% of book price.

    Args:
        book_price: book.price (Decimal or float)

    Returns:
        Rounded Decimal value of rent.
    """
    price = Decimal(str(book_price))
    rent = price * Decimal(str(ActiveConfig.RENT_PERCENT))
    return rent.quantize(Decimal("0.01"))


def calculate_late_fine(book_price, overdue_days: int) -> Decimal:
    """
    Late Fine = (5% of Rent) × overdue_days.

    Args:
        book_price: book.price (Decimal or float)
        overdue_days: number of days past due date

    Returns:
        Total late fine as Decimal.
    """
    if overdue_days <= 0:
        return Decimal("0.00")

    rent = calculate_rent(book_price)
    fine_per_day = rent * Decimal(str(ActiveConfig.LATE_FINE_PERCENT))
    total_fine = fine_per_day * overdue_days
    return total_fine.quantize(Decimal("0.01"))


def calculate_lost_amount(book_price) -> Decimal:
    """
    Lost book charge = full book price.
    No rent, no per day fine.

    Args:
        book_price: book.price (Decimal or float)

    Returns:
        Full book price as Decimal.
    """
    return Decimal(str(book_price)).quantize(Decimal("0.01"))


def compute_account_status(score: int) -> str:
    """
    Derives account status label from behaviour score.

    Args:
        score: integer behaviour score

    Returns:
        'Good' / 'Average' / 'Bad'
    """
    if score >= ActiveConfig.STATUS_GOOD_MIN:
        return "Good"
    elif score >= ActiveConfig.STATUS_AVERAGE_MIN:
        return "Average"
    else:
        return "Bad"


def clamp_score(score: int) -> int:
    """
    Ensures score stays within allowed bounds (0–100).

    Args:
        score: raw score after change

    Returns:
        Score clamped to [SCORE_MIN, SCORE_MAX]
    """
    return max(
        ActiveConfig.SCORE_MIN,
        min(ActiveConfig.SCORE_MAX, score)
    )


def days_until_due(due_date: date) -> int:
    """
    Returns how many days remain until the due date.
    Negative if already overdue.

    Args:
        due_date: the book's due date

    Returns:
        Integer days remaining (can be negative)
    """
    return (due_date - date.today()).days


def format_currency(amount) -> str:
    """
    Formats a numeric amount as Indian Rupee string.

    Args:
        amount: Decimal or float

    Returns:
        String like '₹ 25.50'
    """
    return f"₹ {float(amount):.2f}"