from datetime import datetime
from app import db


class WhatsappLog(db.Model):
    """
    Records every WhatsApp message attempted via Twilio.

    No retry on failure — as per spec.

    status:
        'sent'    → Twilio accepted the message
        'failed'  → Twilio returned an error

    event_type mirrors notification_type:
        'request_approved'
        'request_rejected'
        'due_reminder'
        'overdue_notice'
        'fine_paid'

    error_message is populated only when status is 'failed'.
    """

    __tablename__ = "whatsapp_logs"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Message Details ───────────────────────────────────────────────────────
    event_type = db.Column(db.String(50), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    message_body = db.Column(db.Text, nullable=False)

    # ─── Delivery Status ───────────────────────────────────────────────────────
    status = db.Column(
        db.String(20), default="sent", nullable=False
    )  # sent / failed
    twilio_sid = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    # ─── Timestamp ─────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<WhatsappLog id={self.id} "
            f"student_id={self.student_id} "
            f"event='{self.event_type}' "
            f"status='{self.status}'>"
        )