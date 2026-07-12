from datetime import datetime
from app import db


class Fine(db.Model):
    """
    Tracks all fine records associated with a book issue.

    fine_type values:
        'rent'    → Standard rent charged at return
        'late'    → Late return fine (per day × overdue days)
        'damage'  → Damage fine entered by librarian
        'lost'    → Full book price when book is reported lost

    status:
        'Unpaid'  → Fine not yet paid
        'Paid'    → Fine cleared (online or offline)

    Each fine record is linked to one payment record when paid.
    A single return can generate multiple fine records
    (e.g. rent + late + damage all in one return).
    """

    __tablename__ = "fines"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Keys ──────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    issue_id = db.Column(
        db.Integer,
        db.ForeignKey("book_issues.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Fine Details ──────────────────────────────────────────────────────────
    fine_type = db.Column(
        db.String(20), nullable=False
    )  # rent / late / damage / lost

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # ─── Status ────────────────────────────────────────────────────────────────
    status = db.Column(
        db.String(20), default="Unpaid", nullable=False
    )  # Unpaid / Paid

    # ─── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    # ─── Relationships ─────────────────────────────────────────────────────────
    payment = db.relationship(
        "Payment", backref="fine", uselist=False
    )

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Fine id={self.id} "
            f"type='{self.fine_type}' "
            f"amount={self.amount} "
            f"status='{self.status}'>"
        )