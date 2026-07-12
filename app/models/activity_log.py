from datetime import datetime
from app import db


class ActivityLog(db.Model):
    """
    General activity trail for librarian's audit view.

    Logs significant actions taken by either the librarian or students.
    Not a replacement for specific logs (behaviour_logs, whatsapp_logs)
    but a high-level chronological feed for the librarian dashboard.

    actor_type:
        'student'   → Action performed by student
        'librarian' → Action performed by librarian

    entity_type  → The table/model affected (e.g. 'book', 'student', 'fine')
    entity_id    → The primary key of the affected record
    action       → Short verb describing what happened (e.g. 'approved', 'returned')
    description  → Human readable sentence for display
    """

    __tablename__ = "activity_logs"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Actor ─────────────────────────────────────────────────────────────────
    actor_type = db.Column(
        db.String(20), nullable=False
    )  # student / librarian

    actor_id = db.Column(
        db.Integer, nullable=True
    )  # student.id or null for librarian

    # ─── Entity Affected ───────────────────────────────────────────────────────
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)

    # ─── Action Description ────────────────────────────────────────────────────
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # ─── Timestamp ─────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id} "
            f"actor='{self.actor_type}:{self.actor_id}' "
            f"action='{self.action}'>"
        )