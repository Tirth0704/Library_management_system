from datetime import datetime
from app import db


class BookRecommendation(db.Model):
    """
    Student submitted book recommendations.

    After submission, librarian can:
        Approve  → Add the book to the library
        Reject   → Record rejection

    Student receives an in-app notification of the outcome.

    status:
        'Pending'  → Awaiting librarian decision
        'Approved' → Librarian added book to library
        'Rejected' → Librarian rejected the suggestion
    """

    __tablename__ = "book_recommendations"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Recommendation Fields ─────────────────────────────────────────────────
    book_name = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150), nullable=True)
    reason = db.Column(db.Text, nullable=True)

    # ─── Status ────────────────────────────────────────────────────────────────
    status = db.Column(
        db.String(20), default="Pending", nullable=False
    )  # Pending / Approved / Rejected

    librarian_note = db.Column(db.String(255), nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────────────
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<BookRecommendation id={self.id} "
            f"book='{self.book_name}' "
            f"status='{self.status}'>"
        )