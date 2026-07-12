from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class Student(UserMixin, db.Model):
    """
    Represents a registered student account.

    Behaviour score starts at 100.
    Account status is derived from score:
        80–100 → Good
        50–79  → Average
        0–49   → Bad

    Phone number doubles as WhatsApp contact number.
    Password is always stored hashed via Werkzeug.
    """

    __tablename__ = "students"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Identity Fields ───────────────────────────────────────────────────────
    enrollment_number = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # ─── Academic Fields ───────────────────────────────────────────────────────
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)

    # ─── Behaviour & Status ────────────────────────────────────────────────────
    behaviour_score = db.Column(db.Integer, default=100, nullable=False)
    account_status = db.Column(
        db.String(20), default="Good", nullable=False
    )  # Good / Average / Bad

    # ─── Timestamps ────────────────────────────────────────────────────────────
    joining_date = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ─── Relationships ─────────────────────────────────────────────────────────
    book_requests = db.relationship(
        "BookRequest", backref="student", lazy="dynamic"
    )
    book_issues = db.relationship(
        "BookIssue", backref="student", lazy="dynamic"
    )
    fines = db.relationship(
        "Fine", backref="student", lazy="dynamic"
    )
    payments = db.relationship(
        "Payment", backref="student", lazy="dynamic"
    )
    behaviour_logs = db.relationship(
        "BehaviourLog", backref="student", lazy="dynamic"
    )
    notifications = db.relationship(
        "Notification", backref="student", lazy="dynamic"
    )
    whatsapp_logs = db.relationship(
        "WhatsappLog", backref="student", lazy="dynamic"
    )
    recommendations = db.relationship(
        "BookRecommendation", backref="student", lazy="dynamic"
    )

    # ─── Password Helpers ──────────────────────────────────────────────────────
    def set_password(self, raw_password: str) -> None:
        """Hash and store the password."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify a raw password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    # ─── Status Helpers ────────────────────────────────────────────────────────
    def compute_account_status(self) -> str:
        """
        Derives account label from current behaviour score.
        Keeps account_status field in sync.
        """
        if self.behaviour_score >= 80:
            return "Good"
        elif self.behaviour_score >= 50:
            return "Average"
        else:
            return "Bad"

    def sync_account_status(self) -> None:
        """Call after any score change to keep account_status consistent."""
        self.account_status = self.compute_account_status()

    # ─── Flask-Login Required ─────────────────────────────────────────────────
    def get_id(self) -> str:
        """Flask-Login uses this to store user id in session."""
        return str(self.id)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Student id={self.id} "
            f"name='{self.full_name}' "
            f"score={self.behaviour_score} "
            f"status='{self.account_status}'>"
        )