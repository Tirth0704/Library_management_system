from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.student import Student
from app.models.issue import BookIssue
from app.models.fine import Fine
from app.models.behaviour_log import BehaviourLog
from app.models.activity_log import ActivityLog
from app.utils.decorators import librarian_required
from app.services.behaviour_service import record_librarian_manual
from config import ActiveConfig

librarian_students_bp = Blueprint("librarian_students", __name__,
                                   url_prefix="/librarian")


@librarian_students_bp.route("/students")
@librarian_required
def student_list():
    """Lists all registered students with search."""
    search = request.args.get("q", "").strip()

    if search:
        students = Student.query.filter(
            db.or_(
                Student.full_name.ilike(f"%{search}%"),
                Student.enrollment_number.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%")
            )
        ).order_by(Student.full_name).all()
    else:
        students = Student.query.order_by(Student.full_name).all()

    return render_template(
        "librarian/students/list.html",
        students=students,
        search=search,
        title="Students"
    )


@librarian_students_bp.route("/students/<int:student_id>")
@librarian_required
def student_detail(student_id: int):
    """
    Full student profile view for librarian.
    Shows: profile, active issues, fine history, behaviour log.
    """
    student = Student.query.get_or_404(student_id)

    active_issues = BookIssue.query.filter_by(
        student_id=student.id,
        is_returned=False,
        is_lost=False
    ).all()

    all_fines = Fine.query.filter_by(
        student_id=student.id
    ).order_by(Fine.created_at.desc()).all()

    behaviour_logs = BehaviourLog.query.filter_by(
        student_id=student.id
    ).order_by(BehaviourLog.created_at.desc()).all()

    return render_template(
        "librarian/students/detail.html",
        student=student,
        active_issues=active_issues,
        fines=all_fines,
        behaviour_logs=behaviour_logs,
        title=f"Student: {student.full_name}"
    )


@librarian_students_bp.route("/students/<int:student_id>/score",
                              methods=["POST"])
@librarian_required
def adjust_score(student_id: int):
    """
    Manual behaviour score adjustment by librarian.
    Only permitted when student score < 30 as per spec.
    """
    student = Student.query.get_or_404(student_id)

    if student.behaviour_score >= 30:
        flash(
            "Manual score adjustment is only allowed when score is below 30.",
            "warning"
        )
        return redirect(url_for("librarian_students.student_detail",
                                student_id=student_id))

    try:
        change = int(request.form.get("score_change", 0))
        reason = request.form.get("reason", "").strip()
    except (ValueError, TypeError):
        flash("Invalid score change value.", "danger")
        return redirect(url_for("librarian_students.student_detail",
                                student_id=student_id))

    if change == 0:
        flash("Score change cannot be zero.", "warning")
        return redirect(url_for("librarian_students.student_detail",
                                student_id=student_id))

    record_librarian_manual(student, change, reason)

    log = ActivityLog(
        actor_type="librarian",
        entity_type="student",
        entity_id=student.id,
        action="score_adjusted",
        description=(
            f"Manual score adjustment for {student.full_name}: "
            f"{change:+d}. Reason: {reason}"
        )
    )
    db.session.add(log)
    db.session.commit()

    flash(
        f"Score adjusted by {change:+d} for {student.full_name}.",
        "success"
    )
    return redirect(url_for("librarian_students.student_detail",
                            student_id=student_id))
