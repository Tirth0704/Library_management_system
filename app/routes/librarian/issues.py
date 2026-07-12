from flask import Blueprint, render_template, request
from app.models.issue import BookIssue
from app.models.student import Student
from app.models.book import Book
from app.utils.decorators import librarian_required
from datetime import date

librarian_issues_bp = Blueprint("librarian_issues", __name__,
                                 url_prefix="/librarian")


@librarian_issues_bp.route("/issues")
@librarian_required
def issue_list():
    """
    Lists all active book issues.
    Librarian can filter by overdue status or search by student name.
    """
    filter_type = request.args.get("filter", "all")
    search = request.args.get("q", "").strip()

    issues_query = BookIssue.query.filter_by(
        is_returned=False,
        is_lost=False
    )

    if filter_type == "overdue":
        issues_query = issues_query.filter(
            BookIssue.due_date < date.today()
        )

    issues = issues_query.order_by(BookIssue.due_date.asc()).all()

    # Filter by student name if search query given
    if search:
        issues = [
            i for i in issues
            if search.lower() in (
                Student.query.get(i.student_id).full_name.lower()
            )
        ]

    return render_template(
        "librarian/issues/list.html",
        issues=issues,
        filter_type=filter_type,
        search=search,
        today=date.today(),
        title="Active Issues"
    )