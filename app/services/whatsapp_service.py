from flask import current_app
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app import db
from app.models.whatsapp_log import WhatsappLog


def _get_client():
    """Initializes and returns Twilio client using app config."""
    return Client(
        current_app.config["TWILIO_ACCOUNT_SID"],
        current_app.config["TWILIO_AUTH_TOKEN"]
    )


def _format_whatsapp_number(phone: str) -> str:
    """
    Prepends whatsapp: prefix if not already present.
    Ensures number starts with country code +91 for India.
    """
    phone = phone.strip().replace(" ", "")
    if not phone.startswith("+"):
        phone = "+91" + phone
    if not phone.startswith("whatsapp:"):
        phone = "whatsapp:" + phone
    return phone


def send_whatsapp(student_id: int, phone_number: str,
                   event_type: str, message_body: str,
                   media_url: str = None) -> WhatsappLog:
    """
    Sends a WhatsApp message via Twilio and logs the attempt.

    No retry on failure as per spec.
    Records both success (with twilio_sid) and failure (with error_message).

    Args:
        student_id:   Student's database ID
        phone_number: Student's 10-digit phone number
        event_type:   Event type string for logging
        message_body: Full message text to send
        media_url:    Optional public URL of a media/PDF attachment

    Returns:
        WhatsappLog record (committed).
    """
    to_number = _format_whatsapp_number(phone_number)
    from_number = current_app.config["TWILIO_WHATSAPP_NUMBER"]

    log = WhatsappLog(
        student_id=student_id,
        event_type=event_type,
        to_number=to_number,
        message_body=message_body,
        status="sent"
    )

    try:
        client = _get_client()
        kwargs = {
            "body": message_body,
            "from_": from_number,
            "to": to_number
        }
        if media_url:
            kwargs["media_url"] = [media_url]

        message = client.messages.create(**kwargs)
        log.twilio_sid = message.sid
        log.status = "sent"

    except TwilioRestException as e:
        log.status = "failed"
        log.error_message = str(e)

    except Exception as e:
        log.status = "failed"
        log.error_message = f"Unexpected error: {str(e)}"

    db.session.add(log)
    db.session.commit()
    return log


# ─── Pre-built Message Senders ─────────────────────────────────────────────────

def send_request_approved(student, book_title: str, due_date) -> WhatsappLog:
    message = (
        f"Hello {student.full_name},\n\n"
        f"Your request for *{book_title}* has been approved! "
        f"Please collect the book from the library desk.\n"
        f"Due Date: *{due_date.strftime('%d %b %Y')}*\n\n"
        f"— LibraryHub"
    )
    return send_whatsapp(
        student.id, student.phone_number, "request_approved", message
    )


def send_request_rejected(student, book_title: str, reason: str) -> WhatsappLog:
    message = (
        f"Hello {student.full_name},\n\n"
        f"Your request for *{book_title}* has been rejected.\n"
        f"Reason: {reason}\n\n"
        f"You may re-request after 24 hours.\n\n"
        f"— LibraryHub"
    )
    return send_whatsapp(
        student.id, student.phone_number, "request_rejected", message
    )


def send_due_reminder(student, book_title: str, due_date) -> WhatsappLog:
    message = (
        f"Hello {student.full_name},\n\n"
        f"This is a reminder that *{book_title}* is due *tomorrow* "
        f"({due_date.strftime('%d %b %Y')}).\n"
        f"Please return it on time to avoid late fines.\n\n"
        f"— LibraryHub"
    )
    return send_whatsapp(
        student.id, student.phone_number, "due_reminder", message
    )


def send_overdue_notice(student, book_title: str, due_date) -> WhatsappLog:
    message = (
        f"Hello {student.full_name},\n\n"
        f"*{book_title}* was due on {due_date.strftime('%d %b %Y')} "
        f"and is now *OVERDUE*.\n"
        f"Late fines are being added daily. Please return it immediately.\n\n"
        f"— LibraryHub"
    )
    return send_whatsapp(
        student.id, student.phone_number, "overdue_notice", message
    )


def send_fine_payment_confirmed(student, amount, payment_method: str,
                                payment_id: int = None) -> WhatsappLog:
    """
    Sends a WhatsApp confirmation after a successful fine payment.

    Builds a login-free dynamic URL (e.g. https://app.onrender.com/receipt-pdf/ID)
    that generates and serves the PDF on-the-fly for Twilio to attach inline.

    Args:
        student:        Student object
        amount:         Amount paid
        payment_method: 'razorpay' or 'cash'
        payment_id:     Payment DB ID (optional)
    """
    media_url = None

    if payment_id:
        try:
            base_url = current_app.config.get("BASE_URL", "").rstrip("/")
            if base_url:
                is_local = any(h in base_url for h in ["localhost", "127.0.0.1", "0.0.0.0"])
                if not is_local:
                    media_url = f"{base_url}/receipt-pdf/{payment_id}"
        except Exception:
            pass  # Never crash payment on WhatsApp failure

    message = (
        f"Hello {student.full_name},\n\n"
        f"✅ Your payment of *₹{float(amount):.2f}* has been confirmed "
        f"via {payment_method.capitalize()}.\n"
    )
    if media_url:
        message += "Your digital payment receipt is attached below.\n\n"
    else:
        message += "You can download your receipt from the LibraryHub dashboard.\n\n"
    message += "— LibraryHub"

    return send_whatsapp(
        student.id, student.phone_number, "fine_paid", message, media_url=media_url
    )


def send_book_returned(student, book_title: str, condition: str, total_due: float) -> WhatsappLog:
    message = (
        f"Hello {student.full_name},\n\n"
        f"The return of *{book_title}* has been successfully processed.\n"
        f"Condition: *{condition}*\n"
    )
    if total_due > 0:
        message += f"Total amount due (rent/fines): *₹{total_due:.2f}*\n"
    else:
        message += "No pending dues for this book.\n"
    message += "\nThank you for returning it!\n\n— LibraryHub"
    return send_whatsapp(
        student.id, student.phone_number, "book_returned", message
    )


def send_payment_declined(student, amount, reason: str = None) -> WhatsappLog:
    """Sends a WhatsApp message when a Razorpay payment is declined or fails."""
    message = (
        f"Hello {student.full_name},\n\n"
        f"⚠️ Your payment of *₹{float(amount):.2f}* could not be processed.\n"
    )
    if reason:
        message += f"Reason: {reason}\n"
    message += (
        "\nPlease try again from your fines page or contact the library desk "
        "for assistance.\n\n— LibraryHub"
    )
    return send_whatsapp(
        student.id, student.phone_number, "payment_declined", message
    )