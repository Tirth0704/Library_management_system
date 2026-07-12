from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired


class RazorpayPaymentForm(FlaskForm):
    """
    Hidden form used after Razorpay payment completes.
    Receives payment details from Razorpay JS callback.
    Submitted to backend for verification.
    """
    razorpay_payment_id = HiddenField(
        "Razorpay Payment ID",
        validators=[DataRequired()]
    )
    razorpay_order_id = HiddenField(
        "Razorpay Order ID",
        validators=[DataRequired()]
    )
    razorpay_signature = HiddenField(
        "Razorpay Signature",
        validators=[DataRequired()]
    )
    submit = SubmitField("Confirm Payment")


class MarkOfflineForm(FlaskForm):
    """
    Simple form for librarian to mark a payment as received in cash.
    Just a CSRF-protected submit button.
    """
    submit = SubmitField("Mark as Paid (Cash)")