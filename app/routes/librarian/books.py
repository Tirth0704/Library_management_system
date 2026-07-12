from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models.book import Book
from app.models.category import Category
from app.models.activity_log import ActivityLog
from app.forms.book_forms import AddBookForm, EditBookForm
from app.utils.decorators import librarian_required
from datetime import date

librarian_books_bp = Blueprint("librarian_books", __name__,
                                url_prefix="/librarian")


def _populate_category_choices(form):
    """Helper to fill category dropdown from database."""
    categories = Category.query.order_by(Category.name).all()
    form.category_id.choices = [(0, "Select Category")] + [
        (c.id, c.name) for c in categories
    ]


@librarian_books_bp.route("/books")
@librarian_required
def book_list():
    """Lists all books with search and category filter."""
    query = request.args.get("q", "").strip()
    category_id = request.args.get("category", type=int)

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

    return render_template(
        "librarian/books/list.html",
        books=books,
        categories=categories,
        query=query,
        title="Manage Books"
    )


@librarian_books_bp.route("/books/add", methods=["GET", "POST"])
@librarian_required
def add_book():
    """Librarian adds a new book to inventory."""
    form = AddBookForm()
    _populate_category_choices(form)

    if form.validate_on_submit():
        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            publisher=form.publisher.data.strip() if form.publisher.data else None,
            price=form.price.data,
            total_copies=form.total_copies.data,
            available_copies=form.total_copies.data,
            issued_copies=0,
            category_id=form.category_id.data if form.category_id.data != 0 else None,
            status="Available",
            added_date=date.today()
        )
        db.session.add(book)
        db.session.flush()  # Get book.id before commit

        log = ActivityLog(
            actor_type="librarian",
            entity_type="book",
            entity_id=book.id,
            action="book_added",
            description=f"Added book: {book.title} by {book.author}"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"'{book.title}' added to inventory successfully.", "success")
        return redirect(url_for("librarian_books.book_list"))

    return render_template(
        "librarian/books/add.html",
        form=form,
        title="Add Book"
    )


@librarian_books_bp.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@librarian_required
def edit_book(book_id: int):
    """Librarian edits an existing book."""
    book = Book.query.get_or_404(book_id)
    form = EditBookForm(obj=book)
    _populate_category_choices(form)

    if form.validate_on_submit():
        old_title = book.title
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.publisher = form.publisher.data.strip() if form.publisher.data else None
        book.price = form.price.data

        # If total copies increased, add to available
        new_total = form.total_copies.data
        if new_total > book.total_copies:
            diff = new_total - book.total_copies
            book.available_copies += diff
        elif new_total < book.total_copies:
            diff = book.total_copies - new_total
            book.available_copies = max(0, book.available_copies - diff)

        book.total_copies = new_total
        book.category_id = form.category_id.data if form.category_id.data != 0 else None
        book._sync_status()

        log = ActivityLog(
            actor_type="librarian",
            entity_type="book",
            entity_id=book.id,
            action="book_edited",
            description=f"Edited book: {old_title} → {book.title}"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"'{book.title}' updated successfully.", "success")
        return redirect(url_for("librarian_books.book_list"))

    return render_template(
        "librarian/books/edit.html",
        form=form,
        book=book,
        title=f"Edit: {book.title}"
    )


@librarian_books_bp.route("/books/delete/<int:book_id>", methods=["POST"])
@librarian_required
def delete_book(book_id: int):
    """
    Deletes a book from inventory.
    Only allowed if no active issues exist for this book.
    """
    from app.models.issue import BookIssue
    book = Book.query.get_or_404(book_id)

    active_issues = BookIssue.query.filter_by(
        book_id=book_id,
        is_returned=False
    ).count()

    if active_issues > 0:
        flash(
            f"Cannot delete '{book.title}' — it has {active_issues} active issue(s).",
            "danger"
        )
        return redirect(url_for("librarian_books.book_list"))

    title = book.title
    db.session.delete(book)

    log = ActivityLog(
        actor_type="librarian",
        entity_type="book",
        entity_id=book_id,
        action="book_deleted",
        description=f"Deleted book: {title}"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"'{title}' deleted successfully.", "success")
    return redirect(url_for("librarian_books.book_list"))