from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify, send_from_directory
)
from flask_login import current_user
from app import db
from app.models.fine import Fine
from app.models.payment import Payment
from app.utils.decorators import student_required
from app.services.notification_service import get_unread_count
from app.services.payment_service import (
    create_razorpay_order,
    complete_razorpay_payment
)
from app.services.whatsapp_service import send_payment_declined
from flask import current_app

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/my-fines")
@student_required
def my_fines():
    """Shows all fines (paid and unpaid) for the student."""
    student = current_user

    all_fines = Fine.query.filter_by(
        student_id=student.id
    ).order_by(Fine.created_at.desc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/my_fines.html",
        fines=all_fines,
        unread_count=unread_count,
        title="My Fines"
    )


@payments_bp.route("/pay/<int:fine_id>")
@student_required
def pay_fine(fine_id: int):
    """
    Pay fine page.
    Shows fine details and Razorpay payment button.
    Creates Razorpay order when page loads.
    """
    student = current_user

    fine = Fine.query.filter_by(
        id=fine_id,
        student_id=student.id,
        status="Unpaid"
    ).first_or_404()

    # Create Razorpay order
    try:
        order = create_razorpay_order(fine.amount, fine.id, student.id)
    except Exception as e:
        flash(f"Payment gateway error: {str(e)}", "danger")
        return redirect(url_for("payments.my_fines"))

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/pay_fine.html",
        fine=fine,
        order=order,
        razorpay_key=current_app.config["RAZORPAY_KEY_ID"],
        student=student,
        unread_count=unread_count,
        title="Pay Fine"
    )


@payments_bp.route("/pay/<int:fine_id>/failed", methods=["POST"])
@student_required
def razorpay_failed(fine_id: int):
    """
    Called by JS payment.failed handler when Razorpay reports a failure
    (e.g. card declined, UPI timeout, user dismissed after failed attempt).
    Sends a WhatsApp declined notification and redirects to /my-fines.
    """
    student = current_user
    fine = Fine.query.filter_by(
        id=fine_id,
        student_id=student.id,
        status="Unpaid"
    ).first_or_404()

    error_desc = request.form.get("error_description", "Payment could not be completed.")

    try:
        send_payment_declined(student, fine.amount, reason=error_desc)
    except Exception as e:
        current_app.logger.error(f"WhatsApp declined notification failed: {e}")

    flash("Payment was not completed. Please try again or contact the library desk.", "warning")
    return redirect(url_for("payments.my_fines"))


@payments_bp.route("/pay/<int:fine_id>/razorpay", methods=["POST"])
@student_required
def razorpay_callback(fine_id: int):
    """
    Receives Razorpay payment details after JS callback.
    Verifies signature and records payment.
    """
    student = current_user

    fine = Fine.query.filter_by(
        id=fine_id,
        student_id=student.id,
        status="Unpaid"
    ).first_or_404()

    payment_id = request.form.get("razorpay_payment_id")
    order_id = request.form.get("razorpay_order_id")
    signature = request.form.get("razorpay_signature")

    if not all([payment_id, order_id, signature]):
        flash("Incomplete payment data received.", "danger")
        return redirect(url_for("payments.pay_fine", fine_id=fine_id))

    try:
        payment = complete_razorpay_payment(
            fine=fine,
            student=student,
            order_id=order_id,
            payment_id=payment_id,
            signature=signature
        )
        flash("Payment successful! Receipt is available for download.", "success")
        return redirect(url_for("payments.receipts"))

    except ValueError as e:
        # Signature verification failed — payment was not genuine
        try:
            send_payment_declined(student, fine.amount, reason="Payment verification failed.")
        except Exception:
            pass
        flash(f"Payment verification failed: {str(e)}", "danger")
        return redirect(url_for("payments.pay_fine", fine_id=fine_id))

    except Exception as e:
        # Unexpected server-side error
        try:
            send_payment_declined(student, fine.amount, reason="An unexpected error occurred.")
        except Exception:
            pass
        flash(f"Unexpected error: {str(e)}", "danger")
        return redirect(url_for("payments.pay_fine", fine_id=fine_id))


@payments_bp.route("/receipts")
@student_required
def receipts():
    """Shows all downloadable receipts for the student."""
    student = current_user

    completed_payments = Payment.query.filter_by(
        student_id=student.id,
        status="Completed"
    ).order_by(Payment.completed_at.desc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/receipts.html",
        payments=completed_payments,
        unread_count=unread_count,
        title="My Receipts"
    )


@payments_bp.route("/receipts/<int:payment_id>/download")
@student_required
def download_receipt(payment_id: int):
    """Serves the PDF receipt file for download."""
    student = current_user

    payment = Payment.query.filter_by(
        id=payment_id,
        student_id=student.id,
        status="Completed"
    ).first_or_404()

    if not payment.receipt_path:
        flash("Receipt not found.", "warning")
        return redirect(url_for("payments.receipts"))

    receipts_dir = current_app.config["RECEIPTS_FOLDER"]
    filename = payment.receipt_path.replace("receipts/", "")

    return send_from_directory(
        receipts_dir,
        filename,
        as_attachment=True,
        download_name=f"LibraryHub_Receipt_{payment.id}.pdf"
    )


@payments_bp.route("/receipt-pdf/<int:payment_id>")
def public_receipt_pdf(payment_id: int):
    """
    Public (no-login) route that serves a receipt PDF by payment ID.

    Used exclusively as the Twilio media_url for WhatsApp attachments.
    Twilio fetches this URL server-to-server; it cannot follow a login redirect.

    Only serves receipts whose status is 'Completed'.
    """
    payment = Payment.query.filter_by(
        id=payment_id,
        status="Completed"
    ).first_or_404()

    if not payment.receipt_path:
        from flask import abort
        abort(404)

    receipts_dir = current_app.config["RECEIPTS_FOLDER"]
    filename = payment.receipt_path.replace("receipts/", "")

    return send_from_directory(
        receipts_dir,
        filename,
        as_attachment=False,          # Twilio needs to read it inline
        download_name=f"LibraryHub_Receipt_{payment.id}.pdf"
    )