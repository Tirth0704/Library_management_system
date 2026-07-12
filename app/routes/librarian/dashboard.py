from flask import Blueprint, render_template
from app.models.student import Student
from app.models.book import Book
from app.models.issue import BookIssue
from app.models.fine import Fine
from app.models.request import BookRequest
from app.models.activity_log import ActivityLog
from app.utils.decorators import librarian_required
from datetime import date

librarian_dashboard_bp = Blueprint("librarian_dashboard", __name__,
                                    url_prefix="/librarian")


@librarian_dashboard_bp.route("/dashboard")
@librarian_required
def dashboard():
    """
    Librarian dashboard with summary statistics and recent activity.

    Stats displayed:
    - Total students registered
    - Total books in inventory
    - Currently active issues
    - Overdue issues count
    - Pending requests count
    - Total unpaid fines amount
    - Recent activity log (last 20 entries)
    """
    total_students = Student.query.count()
    total_books = Book.query.count()

    active_issues = BookIssue.query.filter_by(
        is_returned=False, is_lost=False
    ).count()

    # Overdue = issued and due date has passed
    overdue_issues = BookIssue.query.filter(
        BookIssue.is_returned == False,
        BookIssue.is_lost == False,
        BookIssue.due_date < date.today()
    ).count()

    pending_requests = BookRequest.query.filter_by(status="Pending").count()

    from sqlalchemy import func
    from app.models.fine import Fine
    unpaid_total = Fine.query.filter_by(status="Unpaid").with_entities(
        func.sum(Fine.amount)
    ).scalar() or 0

    recent_activity = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).limit(20).all()

    return render_template(
        "librarian/dashboard.html",
        total_students=total_students,
        total_books=total_books,
        active_issues=active_issues,
        overdue_issues=overdue_issues,
        pending_requests=pending_requests,
        unpaid_total=unpaid_total,
        recent_activity=recent_activity,
        title="Librarian Dashboard"
    )