from flask import Blueprint, render_template
from flask_login import current_user
from app.utils.decorators import student_required
from app.models.notification import Notification
from app.services.notification_service import mark_all_read, get_unread_count

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@student_required
def notifications():
    """
    Displays all notifications for the student.
    Marks all as read when page is opened.
    """
    student = current_user

    all_notifications = Notification.query.filter_by(
        student_id=student.id
    ).order_by(Notification.created_at.desc()).all()

    # Mark all as read on page open
    mark_all_read(student.id)

    unread_count = 0  # Just opened, all marked read

    return render_template(
        "student/notifications.html",
        notifications=all_notifications,
        unread_count=unread_count,
        title="Notifications"
    )