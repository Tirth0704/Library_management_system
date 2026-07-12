from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user
from app import db
from app.models.recommendation import BookRecommendation
from app.models.activity_log import ActivityLog
from app.forms.recommendation_forms import RecommendationForm
from app.utils.decorators import student_required
from app.services.notification_service import get_unread_count

recommendations_bp = Blueprint("recommendations", __name__)


@recommendations_bp.route("/recommendations", methods=["GET", "POST"])
@student_required
def recommendations():
    """
    Student can view their past recommendations and submit new ones.

    GET  → Display submission form + student's past recommendations
    POST → Validate and save new recommendation as 'Pending'

    After submission, librarian will review and approve/reject.
    Student receives an in-app notification of the outcome.
    """
    student = current_user
    form = RecommendationForm()

    if form.validate_on_submit():
        # Create recommendation record
        rec = BookRecommendation(
            student_id=student.id,
            book_name=form.book_name.data.strip(),
            author=form.author.data.strip(),
            publisher=(
                form.publisher.data.strip()
                if form.publisher.data else None
            ),
            reason=(
                form.reason.data.strip()
                if form.reason.data else None
            ),
            status="Pending"
        )
        db.session.add(rec)

        # Flush to obtain rec.id for the activity log
        db.session.flush()

        # Log the activity with the now-valid rec.id
        log = ActivityLog(
            actor_type="student",
            actor_id=student.id,
            entity_type="recommendation",
            entity_id=rec.id,
            action="recommendation_submitted",
            description=f"{student.full_name} recommended: {rec.book_name}"
        )
        db.session.add(log)
        db.session.commit()

        flash(
            "Thank you! Your recommendation has been submitted for review.",
            "success"
        )
        return redirect(url_for("recommendations.recommendations"))

    # GET request → fetch student's own recommendations history
    my_recommendations = BookRecommendation.query.filter_by(
        student_id=student.id
    ).order_by(BookRecommendation.submitted_at.desc()).all()

    unread_count = get_unread_count(student.id)

    return render_template(
        "student/recommendations.html",
        form=form,
        recommendations=my_recommendations,
        unread_count=unread_count,
        title="Book Recommendations"
    )