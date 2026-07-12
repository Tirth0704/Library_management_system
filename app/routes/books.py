from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify
)
from flask_login import current_user
from app import db
from app.models.book import Book
from app.models.request import BookRequest
from app.models.issue import BookIssue
from app.models.fine import Fine
from app.utils.decorators import student_required
from app.services.notification_service import get_unread_count
from config import ActiveConfig

books_bp = Blueprint("books", __name__)


@books_bp.route("/books")
@student_required
def book_list():
    """
    Student book search and browse page.
    Supports live search by title or author via AJAX (see search.js).
    Also handles standard query string search for non-JS fallback.
    """
    query = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

    from app.models.category import Category
    categories = Category.query.order_by(Category.name).all()

    books_query = Book.query

    if query:
        books_query = books_query.filter(
            db.or_(
                Book.title.ilike(f"%{query}%"),
                Book.author.ilike(f"%{query}%")
            )
        )

    if category_id:
        books_query = books_query.filter_by(category_id=category_id)

    books = books_query.order_by(Book.title).all()

    # AJAX live search returns JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        results = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "available": b.available_copies > 0,
                "status": b.status
            }
            for b in books
        ]
        return jsonify(results)

    unread_count = get_unread_count(current_user.id)
    return render_template(
        "student/books.html",
        books=books,
        categories=categories,
        query=query,
        unread_count=unread_count,
        title="Browse Books"
    )


@books_bp.route("/books/<int:book_id>")
@student_required
def book_detail(book_id: int):
    """Individual book detail page."""
    book = Book.query.get_or_404(book_id)
    unread_count = get_unread_count(current_user.id)
    return render_template(
        "student/book_detail.html",
        book=book,
        unread_count=unread_count,
        title=book.title
    )


@books_bp.route("/books/<int:book_id>/request", methods=["POST"])
@student_required
def request_book(book_id: int):
    """
    Student requests a book.

    Validations:
    1. Book must exist and be Available
    2. Student must not already have this book issued or pending
    3. Student must not exceed max borrowed books (3)
    4. Student must not have unpaid fines (hold condition)
    5. If previously rejected, 24 hours must have passed
    """
    student = current_user
    book = Book.query.get_or_404(book_id)

    # 1. Book availability
    if book.available_copies < 1 or book.status == "Unavailable":
        flash("This book is currently unavailable.", "warning")
        return redirect(url_for("books.book_detail", book_id=book_id))

    # 2. Already has active issue for this book
    active_issue = BookIssue.query.filter_by(
        student_id=student.id,
        book_id=book_id,
        is_returned=False
    ).first()
    if active_issue:
        flash("You already have this book issued.", "warning")
        return redirect(url_for("books.book_detail", book_id=book_id))

    # 3. Max borrowed check
    active_count = BookIssue.query.filter_by(
        student_id=student.id,
        is_returned=False,
        is_lost=False
    ).count()

    pending_count = BookRequest.query.filter_by(
        student_id=student.id,
        status="Pending"
    ).count()

    if (active_count + pending_count) >= ActiveConfig.MAX_BORROWED_BOOKS:
        flash(
            f"You cannot borrow more than {ActiveConfig.MAX_BORROWED_BOOKS} books at a time.",
            "warning"
        )
        return redirect(url_for("books.book_detail", book_id=book_id))

    # 4. Unpaid fines → Hold
    unpaid = Fine.query.filter_by(student_id=student.id, status="Unpaid").first()
    if unpaid:
        # Create request in Hold status
        req = BookRequest(
            student_id=student.id,
            book_id=book_id,
            status="Hold"
        )
        db.session.add(req)
        db.session.commit()
        flash(
            "Your request is on hold due to unpaid fines. "
            "Clear your dues to activate it.",
            "warning"
        )
        return redirect(url_for("books.book_detail", book_id=book_id))

    # 5. Re-request cooldown after rejection
    last_rejection = BookRequest.query.filter_by(
        student_id=student.id,
        book_id=book_id,
        status="Rejected"
    ).order_by(BookRequest.rejected_at.desc()).first()

    if last_rejection and last_rejection.rejected_at:
        hours_since = (datetime.utcnow() - last_rejection.rejected_at).total_seconds() / 3600
        if hours_since < ActiveConfig.RE_REQUEST_HOURS:
            remaining = int(ActiveConfig.RE_REQUEST_HOURS - hours_since)
            flash(
                f"You must wait {remaining} more hour(s) before re-requesting this book.",
                "warning"
            )
            return redirect(url_for("books.book_detail", book_id=book_id))

    # All checks passed — create Pending request
    req = BookRequest(
        student_id=student.id,
        book_id=book_id,
        status="Pending"
    )
    db.session.add(req)
    db.session.commit()

    flash(f"Request submitted for '{book.title}'. Awaiting librarian approval.", "success")
    return redirect(url_for("requests.my_requests"))