from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import ActiveConfig


# ─── Extensions ────────────────────────────────────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """
    Flask application factory.

    Creates and configures the Flask app, initializes all extensions,
    registers blueprints, sets up user loader, starts the scheduler,
    and creates database tables if they don't exist.

    Returns:
        Configured Flask app instance ready to run.
    """
    app = Flask(__name__)
    app.config.from_object(ActiveConfig)

    # ─── Init Extensions ───────────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ─── Register Student-Facing Blueprints ────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.books import books_bp
    from app.routes.requests import requests_bp
    from app.routes.payments import payments_bp
    from app.routes.notifications import notifications_bp
    from app.routes.recommendations import recommendations_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(recommendations_bp)

    # ─── Register Librarian Blueprints ─────────────────────────────────────────
    from app.routes.librarian.dashboard import librarian_dashboard_bp
    from app.routes.librarian.books import librarian_books_bp
    from app.routes.librarian.categories import librarian_categories_bp
    from app.routes.librarian.requests import librarian_requests_bp
    from app.routes.librarian.issues import librarian_issues_bp
    from app.routes.librarian.returns import librarian_returns_bp
    from app.routes.librarian.students import librarian_students_bp
    from app.routes.librarian.payments import librarian_payments_bp
    from app.routes.librarian.recommendations import librarian_recommendations_bp
    from app.routes.librarian.notifications import librarian_notifications_bp

    app.register_blueprint(librarian_dashboard_bp)
    app.register_blueprint(librarian_books_bp)
    app.register_blueprint(librarian_categories_bp)
    app.register_blueprint(librarian_requests_bp)
    app.register_blueprint(librarian_issues_bp)
    app.register_blueprint(librarian_returns_bp)
    app.register_blueprint(librarian_students_bp)
    app.register_blueprint(librarian_payments_bp)
    app.register_blueprint(librarian_recommendations_bp)
    app.register_blueprint(librarian_notifications_bp)

    # ─── Flask-Login User Loader ───────────────────────────────────────────────
    from app.models.student import Student

    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login calls this with the stored user_id from session.
        Returns the Student object or None.
        Librarian is not a DB user — handled separately via session flag.
        """
        return Student.query.get(int(user_id))

    # ─── Context Processors ────────────────────────────────────────────────────
    @app.context_processor
    def inject_globals():
        """
        Makes these variables available in ALL templates automatically:
          - now  → current datetime (for footer copyright, etc.)
        """
        return {"now": datetime.now()}

    # ─── Start Background Scheduler (APScheduler) ──────────────────────────────
    from app.services.scheduler_service import start_scheduler
    start_scheduler(app)

    # ─── Create Database Tables ────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    return app