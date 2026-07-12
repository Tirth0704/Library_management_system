from datetime import datetime
from app import db


class BookRequest(db.Model):
    """
    Tracks every book request made by a student.

    Status lifecycle:
        Pending  → Librarian has not acted yet
        Approved → Librarian approved, physical handover done,
                   issue record created
        Rejected → Librarian rejected with a reason,
                   student can re-request after 24 hours
        Hold     → Student has unpaid fines,
                   request stays on hold until cleared
        Cancelled → Student cancelled a pending request

    rejection_reason is recorded when librarian rejects.
    rejected_at is used to enforce the 24-hour re-request rule.
    """

    __tablename__ = "book_requests"

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

    # ─── Status ────────────────────────────────────────────────────────────────
    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )  # Pending / Approved / Rejected / Hold / Cancelled

    # ─── Rejection Details ─────────────────────────────────────────────────────
    rejection_reason = db.Column(db.Text, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────────────
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<BookRequest id={self.id} "
            f"student_id={self.student_id} "
            f"book_id={self.book_id} "
            f"status='{self.status}'>"
        )