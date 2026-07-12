from app import db
from app.models.notification import Notification


def create_notification(student_id: int, notification_type: str,
                         title: str, message: str) -> Notification:
    """
    Creates an in-app notification for a student.

    Args:
        student_id:        Target student's ID
        notification_type: One of the defined type strings
        title:             Short headline
        message:           Full notification body

    Returns:
        The created Notification object (not yet committed).
    """
    notification = Notification(
        student_id=student_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False
    )
    db.session.add(notification)
    return notification


def notify_request_approved(student_id: int, book_title: str,
                              due_date) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="request_approved",
        title="Book Request Approved",
        message=(
            f"Your request for '{book_title}' has been approved. "
            f"Please collect the book from the library. "
            f"Due date: {due_date.strftime('%d %b %Y')}."
        )
    )


def notify_request_rejected(student_id: int, book_title: str,
                              reason: str) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="request_rejected",
        title="Book Request Rejected",
        message=(
            f"Your request for '{book_title}' was rejected. "
            f"Reason: {reason}. "
            f"You may re-request after 24 hours."
        )
    )


def notify_due_reminder(student_id: int, book_title: str,
                         due_date) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="due_reminder",
        title="Book Due Tomorrow",
        message=(
            f"Reminder: '{book_title}' is due tomorrow "
            f"({due_date.strftime('%d %b %Y')}). "
            f"Please return it to avoid late fines."
        )
    )


def notify_overdue(student_id: int, book_title: str,
                    due_date) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="overdue_notice",
        title="Book Overdue",
        message=(
            f"'{book_title}' was due on {due_date.strftime('%d %b %Y')} "
            f"and is now overdue. Late fines are accruing. "
            f"Please return it immediately."
        )
    )


def notify_fine_paid(student_id: int, amount, payment_method: str) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="fine_paid",
        title="Payment Confirmed",
        message=(
            f"Your payment of ₹{float(amount):.2f} has been received "
            f"via {payment_method.capitalize()}. "
            f"Download your receipt from the Receipts page."
        )
    )


def notify_recommendation_approved(student_id: int, book_name: str) -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="recommendation_approved",
        title="Recommendation Approved",
        message=(
            f"Great news! Your recommendation for '{book_name}' "
            f"has been approved and added to the library."
        )
    )


def notify_recommendation_rejected(student_id: int, book_name: str,
                                    note: str = "") -> Notification:
    return create_notification(
        student_id=student_id,
        notification_type="recommendation_rejected",
        title="Recommendation Not Approved",
        message=(
            f"Your recommendation for '{book_name}' was not approved. "
            + (f"Librarian note: {note}" if note else "")
        )
    )


def mark_all_read(student_id: int) -> int:
    """
    Marks all unread notifications for a student as read.
    Returns count of updated records.
    """
    count = Notification.query.filter_by(
        student_id=student_id,
        is_read=False
    ).update({"is_read": True})
    db.session.commit()
    return count


def get_unread_count(student_id: int) -> int:
    """Returns count of unread notifications for the student."""
    return Notification.query.filter_by(
        student_id=student_id,
        is_read=False
    ).count()