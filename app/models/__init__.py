# Exposes all models from a single import point.
# Import order matters — resolve foreign key dependencies top to bottom.

from app.models.student import Student
from app.models.category import Category
from app.models.book import Book
from app.models.request import BookRequest
from app.models.issue import BookIssue
from app.models.return_ import BookReturn
from app.models.fine import Fine
from app.models.payment import Payment
from app.models.behaviour_log import BehaviourLog
from app.models.notification import Notification
from app.models.whatsapp_log import WhatsappLog
from app.models.recommendation import BookRecommendation
from app.models.activity_log import ActivityLog

__all__ = [
    "Student",
    "Category",
    "Book",
    "BookRequest",
    "BookIssue",
    "BookReturn",
    "Fine",
    "Payment",
    "BehaviourLog",
    "Notification",
    "WhatsappLog",
    "BookRecommendation",
    "ActivityLog",
]