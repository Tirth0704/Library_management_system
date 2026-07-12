from flask import Blueprint, render_template, request
from app.models.whatsapp_log import WhatsappLog
from app.models.notification import Notification
from app.utils.decorators import librarian_required

librarian_notifications_bp = Blueprint("librarian_notifications", __name__,
                                        url_prefix="/librarian")


@librarian_notifications_bp.route("/notifications")
@librarian_required
def notification_list():
    """
    Librarian view of:
    - All in-app notifications sent to students
    - All WhatsApp message logs (sent/failed)

    Useful for checking delivery and debugging failures.
    """
    tab = request.args.get("tab", "inapp")

    in_app = Notification.query.order_by(
        Notification.created_at.desc()
    ).limit(100).all()

    whatsapp_logs = WhatsappLog.query.order_by(
        WhatsappLog.created_at.desc()
    ).limit(100).all()

    return render_template(
        "librarian/notifications/list.html",
        in_app=in_app,
        whatsapp_logs=whatsapp_logs,
        tab=tab,
        title="Notification Logs"
    )
