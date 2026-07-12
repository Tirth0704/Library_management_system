import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ─── Flask Core ────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key-change-me")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")

    # ─── Database ──────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/libraryhub"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set True to log all SQL queries (debug only)

    # ─── Razorpay ──────────────────────────────────────────────────
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

    # ─── Twilio WhatsApp ───────────────────────────────────────────
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER = os.environ.get(
        "TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"
    )

    # ─── LibraryHub Business Constants ────────────────────────────
    RENT_PERCENT = 0.10            # 10% of book price
    LATE_FINE_PERCENT = 0.05       # 5% of rent per day
    LOAN_PERIOD_DAYS = 14          # Days before book is overdue
    MAX_BORROWED_BOOKS = 3         # Max books a student can borrow at once
    RE_REQUEST_HOURS = 24          # Hours to wait before re-requesting rejected book

    # ─── Behaviour Score Constants ────────────────────────────────
    INITIAL_BEHAVIOUR_SCORE = 100
    SCORE_MAX = 100
    SCORE_MIN = 0

    SCORE_RETURNED_ON_TIME = +2
    SCORE_RETURNED_EARLY = +3
    SCORE_RETURNED_LATE = -5
    SCORE_LOST_BOOK = -25
    SCORE_DAMAGED_BOOK = -20
    SCORE_DAMAGE_FINE_ADDED = -5
    SCORE_CANCELLED_APPROVED = -3
    SCORE_PAID_FINE_IMMEDIATELY = +2

    # ─── Account Status Thresholds ────────────────────────────────
    STATUS_GOOD_MIN = 80
    STATUS_AVERAGE_MIN = 50
    # Below 50 = Bad

    # ─── Librarian Hardcoded Account ──────────────────────────────
    LIBRARIAN_EMAIL = "admin.lms@gmail.com"
    LIBRARIAN_PASSWORD = "admin@#$123"

    # ─── File Storage ─────────────────────────────────────────────
    RECEIPTS_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "app", "static", "receipts"
    )

    # ─── APScheduler ──────────────────────────────────────────────
    SCHEDULER_API_ENABLED = False
    SCHEDULER_TIMEZONE = "Asia/Kolkata"


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False


# Active config selector
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

ActiveConfig = config_map.get(
    os.environ.get("FLASK_ENV", "development"),
    DevelopmentConfig
)