from functools import wraps
from flask import abort, session, redirect, url_for, flash
from flask_login import current_user


def student_required(f):
    """
    Decorator that ensures the current user is a logged-in student.

    Usage:
        @student_required
        def my_view():
            ...

    Blocks librarian from accessing student routes.
    Blocks anonymous users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Librarian uses session flag, not Flask-Login
        if session.get("is_librarian"):
            abort(403)

        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function


def librarian_required(f):
    """
    Decorator that ensures the current session belongs to the librarian.

    The librarian is NOT a DB-backed user.
    Authentication is verified via session flag 'is_librarian'.

    Usage:
        @librarian_required
        def my_view():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_librarian"):
            flash("Librarian access required.", "danger")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function