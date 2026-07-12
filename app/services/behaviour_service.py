from app import db
from app.models.student import Student
from app.models.behaviour_log import BehaviourLog
from app.utils.helpers import clamp_score, compute_account_status
from config import ActiveConfig


def _apply_score_change(student: Student, change: int,
                         event_type: str, description: str = None) -> BehaviourLog:
    """
    Internal function that applies a score delta to a student.

    Records before/after in BehaviourLog.
    Clamps score to [0, 100].
    Updates account_status automatically.
    Does NOT commit — caller must commit.

    Args:
        student:     The Student record to modify
        change:      Integer delta (positive or negative)
        event_type:  One of the defined event type strings
        description: Optional human-readable explanation

    Returns:
        The created BehaviourLog entry.
    """
    score_before = student.behaviour_score
    raw_after = score_before + change
    score_after = clamp_score(raw_after)
    actual_change = score_after - score_before  # may differ from change if clamped

    student.behaviour_score = score_after
    student.account_status = compute_account_status(score_after)

    log = BehaviourLog(
        student_id=student.id,
        score_before=score_before,
        score_change=actual_change,
        score_after=score_after,
        event_type=event_type,
        description=description
    )
    db.session.add(log)
    return log


def record_returned_on_time(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_RETURNED_ON_TIME,
        "returned_on_time",
        f"Returned on time: {book_title}"
    )


def record_returned_early(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_RETURNED_EARLY,
        "returned_early",
        f"Returned early: {book_title}"
    )


def record_returned_late(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_RETURNED_LATE,
        "returned_late",
        f"Returned late: {book_title}"
    )


def record_lost_book(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_LOST_BOOK,
        "lost_book",
        f"Lost book: {book_title}"
    )


def record_damaged_book(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_DAMAGED_BOOK,
        "damaged_book",
        f"Book confirmed damaged: {book_title}"
    )


def record_damage_fine_added(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_DAMAGE_FINE_ADDED,
        "damage_fine_added",
        f"Damage fine applied for: {book_title}"
    )


def record_cancelled_approved(student: Student, book_title: str = "") -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_CANCELLED_APPROVED,
        "cancelled_approved",
        f"Cancelled approved request: {book_title}"
    )


def record_paid_fine_immediately(student: Student) -> BehaviourLog:
    return _apply_score_change(
        student,
        ActiveConfig.SCORE_PAID_FINE_IMMEDIATELY,
        "paid_fine_immediately",
        "Paid fine immediately"
    )


def record_librarian_manual(student: Student, change: int,
                             reason: str = "") -> BehaviourLog:
    """
    Manual score adjustment by librarian.
    Only permitted when score < 30 as per spec.
    Change value is variable (set by librarian).

    Args:
        student: The student to adjust
        change:  Integer delta (positive typically for manual increase)
        reason:  Librarian's explanation
    """
    return _apply_score_change(
        student,
        change,
        "librarian_manual",
        reason or "Librarian manual adjustment"
    )