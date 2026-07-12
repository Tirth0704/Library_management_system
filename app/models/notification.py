from datetime import datetime
from app import db


class Notification(db.Model):
    """
    In-app notifications sent to students.

    notification_type values:
        'request_approved'
        'request_rejected'
        'due_reminder'
        'overdue_notice'
        'fine_paid'
        'recommendation_approved'
        'recommendation_rejected'
        'general'

    is_read → False until student opens notifications page.
    """

    __tablename__ = "notifications"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Content ───────────────────────────────────────────────────────────────
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # ─── Read State ────────────────────────────────────────────────────────────
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # ─── Timestamp ─────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} "
            f"student_id={self.student_id} "
            f"type='{self.notification_type}' "
            f"read={self.is_read}>"
        )