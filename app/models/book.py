from datetime import date, datetime
from app import db


class Book(db.Model):
    """
    Represents a book in the library inventory.

    Price is stored as a Decimal and is used to calculate:
        Rent      = 10% of price
        Late Fine = 5% of Rent per overdue day

    available_copies and issued_copies are managed automatically
    when requests are approved and books are returned.

    Status field:
        'Available'   → at least one copy available
        'Unavailable' → all copies are issued out
    """

    __tablename__ = "books"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Book Information ──────────────────────────────────────────────────────
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # ─── Inventory ─────────────────────────────────────────────────────────────
    total_copies = db.Column(db.Integer, default=1, nullable=False)
    available_copies = db.Column(db.Integer, default=1, nullable=False)
    issued_copies = db.Column(db.Integer, default=0, nullable=False)

    # ─── Category (FK) ─────────────────────────────────────────────────────────
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True
    )

    # ─── Status & Dates ────────────────────────────────────────────────────────
    status = db.Column(
        db.String(20), default="Available", nullable=False
    )  # Available / Unavailable
    added_date = db.Column(db.Date, default=date.today, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ─── Relationships ─────────────────────────────────────────────────────────
    book_requests = db.relationship(
        "BookRequest", backref="book", lazy="dynamic"
    )
    book_issues = db.relationship(
        "BookIssue", backref="book", lazy="dynamic"
    )

    # ─── Computed Properties ───────────────────────────────────────────────────
    @property
    def rent(self) -> float:
        """Rent = 10% of book price."""
        return round(float(self.price) * 0.10, 2)

    @property
    def fine_per_day(self) -> float:
        """Late fine per day = 5% of rent."""
        return round(self.rent * 0.05, 2)

    # ─── Inventory Helpers ─────────────────────────────────────────────────────
    def issue_copy(self) -> bool:
        """
        Decrement available, increment issued.
        Returns False if no copies available.
        """
        if self.available_copies < 1:
            return False
        self.available_copies -= 1
        self.issued_copies += 1
        self._sync_status()
        return True

    def return_copy(self) -> None:
        """Increment available, decrement issued after return."""
        self.issued_copies = max(0, self.issued_copies - 1)
        self.available_copies = min(
            self.total_copies,
            self.available_copies + 1
        )
        self._sync_status()

    def _sync_status(self) -> None:
        """Keep status field in sync with available_copies."""
        self.status = "Available" if self.available_copies > 0 else "Unavailable"

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Book id={self.id} "
            f"title='{self.title}' "
            f"available={self.available_copies}/{self.total_copies}>"
        )