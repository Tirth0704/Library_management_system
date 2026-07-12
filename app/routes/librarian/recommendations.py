from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.recommendation import BookRecommendation
from app.models.activity_log import ActivityLog
from app.utils.decorators import librarian_required
from app.services.notification_service import (
    notify_recommendation_approved,
    notify_recommendation_rejected
)

librarian_recommendations_bp = Blueprint("librarian_recommendations", __name__,
                                          url_prefix="/librarian")


@librarian_recommendations_bp.route("/recommendations")
@librarian_required
def recommendation_list():
    """Lists all student book recommendations."""
    status_filter = request.args.get("status", "Pending")

    recommendations = BookRecommendation.query.filter_by(
        status=status_filter
    ).order_by(BookRecommendation.submitted_at.desc()).all()

    return render_template(
        "librarian/recommendations/list.html",
        recommendations=recommendations,
        status_filter=status_filter,
        title="Book Recommendations"
    )


@librarian_recommendations_bp.route(
    "/recommendations/<int:rec_id>/approve", methods=["POST"]
)
@librarian_required
def approve_recommendation(rec_id: int):
    """
    Approves a recommendation.
    Sends in-app notification to student.
    Librarian adds the book to inventory separately via /librarian/books/add.
    """
    rec = BookRecommendation.query.get_or_404(rec_id)

    if rec.status != "Pending":
        flash("This recommendation has already been reviewed.", "warning")
        return redirect(url_for("librarian_recommendations.recommendation_list"))

    rec.status = "Approved"
    rec.reviewed_at = datetime.utcnow()
    rec.librarian_note = request.form.get("note", "").strip() or None

    log = ActivityLog(
        actor_type="librarian",
        entity_type="recommendation",
        entity_id=rec.id,
        action="recommendation_approved",
        description=f"Approved recommendation: {rec.book_name}"
    )
    db.session.add(log)
    db.session.commit()

    notify_recommendation_approved(rec.student_id, rec.book_name)
    db.session.commit()

    flash(f"Recommendation for '{rec.book_name}' approved.", "success")
    return redirect(url_for("librarian_recommendations.recommendation_list"))


@librarian_recommendations_bp.route(
    "/recommendations/<int:rec_id>/reject", methods=["POST"]
)
@librarian_required
def reject_recommendation(rec_id: int):
    """Rejects a recommendation and notifies student."""
    rec = BookRecommendation.query.get_or_404(rec_id)

    if rec.status != "Pending":
        flash("This recommendation has already been reviewed.", "warning")
        return redirect(url_for("librarian_recommendations.recommendation_list"))

    rec.status = "Rejected"
    rec.reviewed_at = datetime.utcnow()
    rec.librarian_note = request.form.get("note", "").strip() or None

    log = ActivityLog(
        actor_type="librarian",
        entity_type="recommendation",
        entity_id=rec.id,
        action="recommendation_rejected",
        description=f"Rejected recommendation: {rec.book_name}"
    )
    db.session.add(log)
    db.session.commit()

    notify_recommendation_rejected(
        rec.student_id, rec.book_name, rec.librarian_note or ""
    )
    db.session.commit()

    flash(f"Recommendation for '{rec.book_name}' rejected.", "info")
    return redirect(url_for("librarian_recommendations.recommendation_list"))
