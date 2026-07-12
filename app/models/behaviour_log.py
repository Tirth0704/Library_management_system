from datetime import datetime
from app import db


class BehaviourLog(db.Model):
    """
    Immutable log of every behaviour score change for a student.

    Every score change (positive or negative) creates one record here.
    This gives the librarian a full audit trail.

    score_before  → Score value before the event
    score_change  → The delta applied (can be negative)
    score_after   → Score value after the event

    event_type values (matching spec):
        'returned_on_time'
        'returned_early'
        'returned_late'
        'lost_book'
        'damaged_book'
        'damage_fine_added'
        'cancelled_approved'
        'paid_fine_immediately'
        'librarian_manual'
    """

    __tablename__ = "behaviour_logs"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Key ───────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )

    # ─── Score Snapshot ────────────────────────────────────────────────────────
    score_before = db.Column(db.Integer, nullable=False)
    score_change = db.Column(db.Integer, nullable=False)
    score_after = db.Column(db.Integer, nullable=False)

    # ─── Event Details ─────────────────────────────────────────────────────────
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # ─── Timestamp ─────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<BehaviourLog id={self.id} "
            f"student_id={self.student_id} "
            f"event='{self.event_type}' "
            f"change={self.score_change:+d} "
            f"after={self.score_after}>"
        )