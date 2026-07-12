from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, session
)
from flask_login import login_user, logout_user, current_user
from app import db
from app.models.student import Student
from app.models.activity_log import ActivityLog
from app.forms.auth_forms import LoginForm, RegisterForm
from config import ActiveConfig

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    """
    Root route — smart redirect based on session state.
    """
    if session.get("is_librarian"):
        return redirect(url_for("librarian_dashboard.dashboard"))
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Unified login for students and librarian."""
    if session.get("is_librarian"):
        return redirect(url_for("librarian_dashboard.dashboard"))
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        # Librarian login
        if (email == ActiveConfig.LIBRARIAN_EMAIL.lower()
                and password == ActiveConfig.LIBRARIAN_PASSWORD):
            session["is_librarian"] = True
            session.permanent = True

            log = ActivityLog(
                actor_type="librarian",
                action="login",
                description="Librarian logged in."
            )
            db.session.add(log)
            db.session.commit()

            flash("Welcome, Librarian!", "success")
            return redirect(url_for("librarian_dashboard.dashboard"))

        # Student login
        student = Student.query.filter_by(email=email).first()

        if student and student.check_password(password):
            login_user(student, remember=form.remember_me.data)

            log = ActivityLog(
                actor_type="student",
                actor_id=student.id,
                action="login",
                description=f"{student.full_name} logged in."
            )
            db.session.add(log)
            db.session.commit()

            flash(f"Welcome back, {student.full_name}!", "success")

            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("student.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form, title="Login")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Student self-registration."""
    if session.get("is_librarian"):
        return redirect(url_for("librarian_dashboard.dashboard"))
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))

    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        enrollment = form.enrollment_number.data.strip().upper()

        if Student.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return render_template("auth/register.html", form=form, title="Register")

        if Student.query.filter_by(enrollment_number=enrollment).first():
            flash("This enrollment number is already registered.", "danger")
            return render_template("auth/register.html", form=form, title="Register")

        student = Student(
            full_name=form.full_name.data.strip(),
            enrollment_number=enrollment,
            email=email,
            phone_number=form.phone_number.data.strip(),
            department=form.department.data,
            semester=form.semester.data,
            behaviour_score=ActiveConfig.INITIAL_BEHAVIOUR_SCORE,
            account_status="Good"
        )
        student.set_password(form.password.data)

        db.session.add(student)
        db.session.flush()

        log = ActivityLog(
            actor_type="student",
            actor_id=student.id,
            entity_type="student",
            entity_id=student.id,
            action="registered",
            description=f"New student registered: {student.full_name} ({student.email})"
        )
        db.session.add(log)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form, title="Register")


@auth_bp.route("/logout")
def logout():
    """Logs out student or librarian."""
    if session.get("is_librarian"):
        log = ActivityLog(
            actor_type="librarian",
            action="logout",
            description="Librarian logged out."
        )
        db.session.add(log)
        db.session.commit()

    elif current_user.is_authenticated:
        student_id = current_user.id
        student_name = current_user.full_name
        logout_user()

        log = ActivityLog(
            actor_type="student",
            actor_id=student_id,
            action="logout",
            description=f"{student_name} logged out."
        )
        db.session.add(log)
        db.session.commit()

    # Save the remember flag set by logout_user() to clear remember-me cookies
    remember_val = session.get("_remember")
    session.clear()
    if remember_val:
        session["_remember"] = remember_val

    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))