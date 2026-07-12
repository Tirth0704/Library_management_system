from datetime import datetime
from app import db


class Category(db.Model):
    """
    Flat list of book categories.
    Each book belongs to one category (foreign key).
    Librarian manages categories via the librarian panel.
    """

    __tablename__ = "categories"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Fields ────────────────────────────────────────────────────────────────
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Relationships ─────────────────────────────────────────────────────────
    books = db.relationship("Book", backref="category", lazy="dynamic")

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"<Category id={self.id} name='{self.name}'>"