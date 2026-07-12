from datetime import datetime, date, timedelta
from app import db
from config import ActiveConfig


class BookIssue(db.Model):
    """
    Created when a librarian physically hands a book to a student
    after approving the request.

    issue_date    → Date librarian entered (physical handover date)
    due_date      → issue_date + 14 days (LOAN_PERIOD_DAYS)
    return_date   → Filled when student returns the book

    is_returned   → False until return is processed
    is_lost       → True if student reports book as lost

    Status:
        Issued   → Active, student has the book
        Returned → Book returned (on time or late)
        Lost     → Reported lost by student via librarian
        Overdue  → Still issued after due date (computed, not stored)
    """

    __tablename__ = "book_issues"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Keys ──────────────────────────────────────────────────────────
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
    request_id = db.Column(
        db.Integer,
        db.ForeignKey("book_requests.id", ondelete="SET NULL"),
        nullable=True
    )

    # ─── Issue Details ─────────────────────────────────────────────────────────
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)

    # ─── Flags ─────────────────────────────────────────────────────────────────
    is_returned = db.Column(db.Boolean, default=False, nullable=False)
    is_lost = db.Column(db.Boolean, default=False, nullable=False)

    # ─── Status ────────────────────────────────────────────────────────────────
    status = db.Column(
        db.String(20), default="Issued", nullable=False
    )  # Issued / Returned / Lost

    # ─── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ─── Relationships ─────────────────────────────────────────────────────────
    fines = db.relationship("Fine", backref="issue", lazy="dynamic")
    book_return = db.relationship(
        "BookReturn", backref="issue", uselist=False
    )

    # ─── Computed Properties ───────────────────────────────────────────────────
    @property
    def is_overdue(self) -> bool:
        """True if today is past the due date and book not returned."""
        if self.is_returned or self.is_lost:
            return False
        return date.today() > self.due_date

    @property
    def overdue_days(self) -> int:
        """
        Number of days past due date.
        Returns 0 if not overdue or already returned.
        """
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    def set_due_date(self) -> None:
        """
        Automatically compute due_date from issue_date.
        Called when issue record is first created.
        """
        loan_period = ActiveConfig.LOAN_PERIOD_DAYS
        if isinstance(self.issue_date, date):
            self.due_date = self.issue_date + timedelta(days=loan_period)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<BookIssue id={self.id} "
            f"student_id={self.student_id} "
            f"book_id={self.book_id} "
            f"due={self.due_date} "
            f"returned={self.is_returned}>"
        )