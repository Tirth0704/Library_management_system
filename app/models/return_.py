from datetime import datetime, date
from app import db


class BookReturn(db.Model):
    """
    Records a completed book return transaction.

    Created by librarian when student brings back the book.

    condition field captures the state of the book at return:
        'Good'     → No damage
        'Damaged'  → Librarian confirms damage
        'Lost'     → Student lost the book

    damage_fine is the variable fine amount set by librarian
    for damaged books (on top of rent).

    One BookIssue has at most one BookReturn (uselist=False on issue side).
    """

    __tablename__ = "book_returns"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Keys ──────────────────────────────────────────────────────────
    issue_id = db.Column(
        db.Integer,
        db.ForeignKey("book_issues.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One return per issue
    )
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Return Details ────────────────────────────────────────────────────────
    return_date = db.Column(db.Date, nullable=False, default=date.today)
    condition = db.Column(
        db.String(20), default="Good", nullable=False
    )  # Good / Damaged / Lost

    # ─── Financials ────────────────────────────────────────────────────────────
    rent_charged = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    late_fine = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    damage_fine = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    lost_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    total_due = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)

    # ─── Notes ─────────────────────────────────────────────────────────────────
    librarian_notes = db.Column(db.Text, nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<BookReturn id={self.id} "
            f"issue_id={self.issue_id} "
            f"condition='{self.condition}' "
            f"total_due={self.total_due}>"
        )