from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.models.book import Book
from app.models.issue import BookIssue
from app.models.notification import Notification
from app.forms.student_forms import EditProfileForm
from app.utils.decorators import student_required
from app.services.notification_service import get_unread_count
from app.models.activity_log import ActivityLog

student_bp = Blueprint("student", __name__)


@student_bp.route("/dashboard")
@student_required
def dashboard():
    """
    Student dashboard.

    Shows:
    - Summary cards (active books, pending requests, unpaid fines, score)
    - Newly added books (sorted by date, most recent first)
    - Unread notification count
    """
    from app.models.fine import Fine
    from app.models.request import BookRequest

    student = current_user

    # Active issues
    active_issues = BookIssue.query.filter_by(
        student_id=student.id,
        is_returned=False,
        is_lost=False
    ).all()

    # Pending requests
    pending_requests = BookRequest.query.filter_by(
        student_id=student.id,
        status="Pending"
    ).count()

    # Unpaid fines count & total
    from app.services.fine_service import get_unpaid_fines, get_total_unpaid_amount
    unpaid_fines = get_unpaid_fines(student.id)
    total_unpaid = get_total_unpaid_amount(student.id)

    # Newly added books (last 10)
    new_books = Book.query.order_by(Book.added_date.desc()).limit(10).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/dashboard.html",
        student=student,
        active_issues=active_issues,
        pending_requests=pending_requests,
        unpaid_fines=unpaid_fines,
        total_unpaid=total_unpaid,
        new_books=new_books,
        unread_count=unread_count,
        title="My Dashboard"
    )


@student_bp.route("/profile")
@student_required
def profile():
    """Student's profile view page."""
    unread_count = get_unread_count(current_user.id)
    return render_template(
        "student/profile.html",
        student=current_user,
        unread_count=unread_count,
        title="My Profile"
    )


@student_bp.route("/profile/edit", methods=["GET", "POST"])
@student_required
def edit_profile():
    """
    Student can update full_name, phone_number, department, semester.
    Email and enrollment number are locked post-registration.
    """
    student = current_user
    form = EditProfileForm(obj=student)

    if form.validate_on_submit():
        student.full_name = form.full_name.data.strip()
        student.phone_number = form.phone_number.data.strip()
        student.department = form.department.data
        student.semester = form.semester.data

        db.session.commit()

        log = ActivityLog(
            actor_type="student",
            actor_id=student.id,
            action="profile_updated",
            description=f"{student.full_name} updated their profile."
        )
        db.session.add(log)
        db.session.commit()

        flash("Profile updated successfully.", "success")
        return redirect(url_for("student.profile"))

    unread_count = get_unread_count(current_user.id)
    return render_template(
        "student/profile.html",
        student=student,
        form=form,
        edit_mode=True,
        unread_count=unread_count,
        title="Edit Profile"
    )