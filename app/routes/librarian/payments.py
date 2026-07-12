from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.payment import Payment
from app.models.fine import Fine
from app.models.student import Student
from app.utils.decorators import librarian_required
from app.services.payment_service import complete_cash_payment

librarian_payments_bp = Blueprint("librarian_payments", __name__,
                                   url_prefix="/librarian")


@librarian_payments_bp.route("/payments")
@librarian_required
def payment_list():
    """Lists all payment records with optional filters."""
    status_filter = request.args.get("status", "all")
    method_filter = request.args.get("method", "all")

    payments_query = Payment.query

    if status_filter != "all":
        payments_query = payments_query.filter_by(status=status_filter)

    if method_filter != "all":
        payments_query = payments_query.filter_by(payment_method=method_filter)

    payments = payments_query.order_by(Payment.created_at.desc()).all()

    return render_template(
        "librarian/payments/list.html",
        payments=payments,
        status_filter=status_filter,
        method_filter=method_filter,
        title="Payments"
    )


@librarian_payments_bp.route("/payments/<int:fine_id>/mark-offline",
                              methods=["POST"])
@librarian_required
def mark_offline(fine_id: int):
    """
    Librarian marks a fine as paid in cash (offline payment).
    Triggers same post-payment logic as online:
    - Receipt generation
    - Behaviour score update
    - Notifications
    """
    fine = Fine.query.filter_by(id=fine_id, status="Unpaid").first_or_404()
    student = Student.query.get(fine.student_id)

    try:
        payment = complete_cash_payment(fine=fine, student=student)
        flash(
            f"Cash payment of ₹{float(fine.amount):.2f} recorded for "
            f"{student.full_name}.",
            "success"
        )
    except Exception as e:
        flash(f"Error recording payment: {str(e)}", "danger")

    return redirect(url_for("librarian_payments.payment_list"))
