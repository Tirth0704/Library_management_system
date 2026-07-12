import razorpay
import hmac
import hashlib
from decimal import Decimal
from datetime import datetime
from flask import current_app
from app import db
from app.models.payment import Payment
from app.models.fine import Fine
from app.services.fine_service import mark_fine_paid
from app.services.behaviour_service import record_paid_fine_immediately
from app.services.notification_service import notify_fine_paid
from app.services.whatsapp_service import send_fine_payment_confirmed
from app.models.student import Student


def get_razorpay_client():
    """Returns an authenticated Razorpay client instance."""
    return razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        )
    )


def create_razorpay_order(amount: Decimal, fine_id: int,
                           student_id: int) -> dict:
    """
    Creates a Razorpay order for the given fine amount.

    Razorpay requires amount in paise (1 INR = 100 paise).

    Args:
        amount:     Fine amount in INR
        fine_id:    The fine being paid
        student_id: The student paying

    Returns:
        Razorpay order dict containing 'id', 'amount', 'currency'.

    Raises:
        Exception if Razorpay API call fails.
    """
    client = get_razorpay_client()
    amount_paise = int(float(amount) * 100)

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"fine_{fine_id}_student_{student_id}",
        "notes": {
            "fine_id": str(fine_id),
            "student_id": str(student_id)
        }
    }

    order = client.order.create(data=order_data)
    return order


def verify_razorpay_signature(order_id: str, payment_id: str,
                               signature: str) -> bool:
    """
    Verifies the Razorpay payment signature using HMAC-SHA256.

    Args:
        order_id:   Razorpay order ID
        payment_id: Razorpay payment ID returned on success
        signature:  Razorpay signature to verify

    Returns:
        True if signature is valid, False otherwise.
    """
    secret = current_app.config["RAZORPAY_KEY_SECRET"].encode("utf-8")
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    # Both must be the same type (str); Razorpay signature is a hex string
    return hmac.compare_digest(expected, str(signature))


def complete_razorpay_payment(fine: Fine, student: Student,
                               order_id: str, payment_id: str,
                               signature: str) -> Payment:
    """
    Verifies and records a completed Razorpay payment.

    Steps:
        1. Verify signature
        2. Create Payment record (Completed)
        3. Mark fine as Paid
        4. Update behaviour score (+2 for immediate payment)
        5. Create in-app notification
        6. Send WhatsApp confirmation
        7. Generate PDF receipt

    Args:
        fine:       The Fine record being paid
        student:    The Student making payment
        order_id:   From Razorpay
        payment_id: From Razorpay
        signature:  From Razorpay

    Returns:
        The Payment record.

    Raises:
        ValueError if signature verification fails.
    """
    if not verify_razorpay_signature(order_id, payment_id, signature):
        raise ValueError("Payment signature verification failed.")

    now = datetime.utcnow()

    # Create payment record
    payment = Payment(
        student_id=student.id,
        fine_id=fine.id,
        amount=fine.amount,
        payment_method="razorpay",
        status="Completed",
        razorpay_order_id=order_id,
        razorpay_payment_id=payment_id,
        razorpay_signature=signature,
        completed_at=now
    )
    db.session.add(payment)

    # Mark fine paid
    mark_fine_paid(fine, paid_at=now)

    # Behaviour score
    record_paid_fine_immediately(student)

    db.session.commit()

    # Generate receipt
    receipt_path = None
    try:
        from app.services.receipt_service import generate_receipt
        receipt_path = generate_receipt(payment, fine, student)
        payment.receipt_path = receipt_path
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Receipt generation failed: {e}")

    # In-app notification
    try:
        notify_fine_paid(student.id, fine.amount, "razorpay")
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"In-app notification failed: {e}")

    # WhatsApp confirmation (never crash the payment on WA failure)
    try:
        send_fine_payment_confirmed(
            student, fine.amount, "razorpay",
            receipt_path=receipt_path,
            payment_id=payment.id
        )
    except Exception as e:
        current_app.logger.error(f"WhatsApp payment confirmation failed: {e}")

    return payment


def complete_cash_payment(fine: Fine, student: Student) -> Payment:
    """
    Records a cash payment marked offline by the librarian.

    Steps:
        1. Create Payment record (Completed, method=cash)
        2. Mark fine as Paid
        3. Update behaviour score (+2 for immediate payment)
        4. Create in-app notification
        5. Send WhatsApp confirmation
        6. Generate PDF receipt

    Args:
        fine:    The Fine record being paid
        student: The Student making payment

    Returns:
        The Payment record.
    """
    now = datetime.utcnow()

    payment = Payment(
        student_id=student.id,
        fine_id=fine.id,
        amount=fine.amount,
        payment_method="cash",
        status="Completed",
        completed_at=now
    )
    db.session.add(payment)

    mark_fine_paid(fine, paid_at=now)
    record_paid_fine_immediately(student)

    db.session.commit()

    # Generate receipt
    receipt_path = None
    try:
        from app.services.receipt_service import generate_receipt
        receipt_path = generate_receipt(payment, fine, student)
        payment.receipt_path = receipt_path
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Receipt generation failed: {e}")

    # In-app notification
    try:
        notify_fine_paid(student.id, fine.amount, "cash")
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"In-app notification failed: {e}")

    # WhatsApp confirmation
    try:
        send_fine_payment_confirmed(
            student, fine.amount, "cash",
            receipt_path=receipt_path,
            payment_id=payment.id
        )
    except Exception as e:
        current_app.logger.error(f"WhatsApp payment confirmation failed: {e}")

    return payment