from datetime import date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz


def start_scheduler(app):
    """
    Initializes and starts APScheduler with two daily tasks:

    1. due_date_reminder_job  → Runs daily at 09:00 IST
       Finds all issues due tomorrow and sends reminder.

    2. overdue_notice_job     → Runs daily at 09:30 IST
       Finds all issues that became overdue today (first day only).
       Sends one-time overdue notice.

    Scheduler runs in background thread.
    All jobs run inside Flask app context.
    """
    scheduler = BackgroundScheduler(
        timezone=pytz.timezone(app.config.get("SCHEDULER_TIMEZONE", "Asia/Kolkata"))
    )

    scheduler.add_job(
        func=lambda: _run_in_context(app, _due_date_reminder_job),
        trigger=CronTrigger(hour=9, minute=0),
        id="due_date_reminder",
        name="Due Date Reminder",
        replace_existing=True
    )

    scheduler.add_job(
        func=lambda: _run_in_context(app, _overdue_notice_job),
        trigger=CronTrigger(hour=9, minute=30),
        id="overdue_notice",
        name="Overdue Notice",
        replace_existing=True
    )

    scheduler.start()
    return scheduler


def _run_in_context(app, job_fn):
    """Wraps a job function inside Flask app context."""
    with app.app_context():
        job_fn()


def _due_date_reminder_job():
    """
    Sends WhatsApp + in-app reminder for books due tomorrow.

    Queries all active (not returned) issues where due_date = tomorrow.
    """
    from app.models.issue import BookIssue
    from app.models.book import Book
    from app.models.student import Student
    from app.services.whatsapp_service import send_due_reminder
    from app.services.notification_service import notify_due_reminder
    from app import db

    tomorrow = date.today() + timedelta(days=1)

    issues = BookIssue.query.filter_by(
        is_returned=False,
        is_lost=False
    ).filter(
        BookIssue.due_date == tomorrow
    ).all()

    for issue in issues:
        student = Student.query.get(issue.student_id)
        book = Book.query.get(issue.book_id)

        if student and book:
            try:
                notify_due_reminder(student.id, book.title, issue.due_date)
                db.session.commit()
                send_due_reminder(student, book.title, issue.due_date)
            except Exception as e:
                print(f"[Scheduler] Due reminder failed for issue {issue.id}: {e}")


def _overdue_notice_job():
    """
    Sends one-time overdue notice for books that became overdue today.

    Only fires on the FIRST day of overdue (due_date = yesterday).
    To avoid repeat notices, checks that no overdue WhatsApp was already sent.
    """
    from app.models.issue import BookIssue
    from app.models.book import Book
    from app.models.student import Student
    from app.models.whatsapp_log import WhatsappLog
    from app.services.whatsapp_service import send_overdue_notice
    from app.services.notification_service import notify_overdue
    from app import db

    yesterday = date.today() - timedelta(days=1)

    issues = BookIssue.query.filter_by(
        is_returned=False,
        is_lost=False
    ).filter(
        BookIssue.due_date == yesterday
    ).all()

    for issue in issues:
        student = Student.query.get(issue.student_id)
        book = Book.query.get(issue.book_id)

        if not student or not book:
            continue

        # Check if overdue notice already sent for this issue
        already_sent = WhatsappLog.query.filter_by(
            student_id=student.id,
            event_type="overdue_notice"
        ).filter(
            WhatsappLog.message_body.contains(book.title)
        ).first()

        if already_sent:
            continue

        try:
            notify_overdue(student.id, book.title, issue.due_date)
            db.session.commit()
            send_overdue_notice(student, book.title, issue.due_date)
        except Exception as e:
            print(f"[Scheduler] Overdue notice failed for issue {issue.id}: {e}")