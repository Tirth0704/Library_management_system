from datetime import datetime
from app import db


class Payment(db.Model):
    """
    Records every payment made by a student.

    payment_method:
        'razorpay' → Online via Razorpay (UPI, Card, Net Banking)
        'cash'     → Offline, librarian clicks 'Paid Offline'

    status:
        'Pending'   → Razorpay order created, payment not confirmed yet
        'Completed' → Payment confirmed and recorded
        'Failed'    → Razorpay payment failed

    razorpay_order_id     → Created before payment
    razorpay_payment_id   → Returned by Razorpay on success
    razorpay_signature    → Used for verification

    For cash payments, razorpay fields are all null.
    receipt_path stores relative path to generated PDF in static/receipts/.
    """

    __tablename__ = "payments"

    # ─── Primary Key ───────────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ─── Foreign Keys ──────────────────────────────────────────────────────────
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False
    )
    fine_id = db.Column(
        db.Integer,
        db.ForeignKey("fines.id", ondelete="SET NULL"),
        nullable=True
    )

    # ─── Payment Details ───────────────────────────────────────────────────────
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(
        db.String(20), nullable=False
    )  # razorpay / cash

    status = db.Column(
        db.String(20), default="Pending", nullable=False
    )  # Pending / Completed / Failed

    # ─── Razorpay Fields ───────────────────────────────────────────────────────
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    razorpay_payment_id = db.Column(db.String(100), nullable=True)
    razorpay_signature = db.Column(db.String(255), nullable=True)

    # ─── Receipt ───────────────────────────────────────────────────────────────
    receipt_path = db.Column(db.String(255), nullable=True)

    # ─── Timestamps ────────────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # ─── Representation ───────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} "
            f"amount={self.amount} "
            f"method='{self.payment_method}' "
            f"status='{self.status}'>"
        )