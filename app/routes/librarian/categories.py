from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models.category import Category
from app.forms.book_forms import AddCategoryForm
from app.utils.decorators import librarian_required

librarian_categories_bp = Blueprint("librarian_categories", __name__,
                                     url_prefix="/librarian")


@librarian_categories_bp.route("/categories")
@librarian_required
def category_list():
    """Lists all book categories with book count per category."""
    categories = Category.query.order_by(Category.name).all()
    form = AddCategoryForm()
    return render_template(
        "librarian/categories/list.html",
        categories=categories,
        form=form,
        title="Manage Categories"
    )


@librarian_categories_bp.route("/categories/add", methods=["POST"])
@librarian_required
def add_category():
    """Adds a new book category."""
    form = AddCategoryForm()

    if form.validate_on_submit():
        existing = Category.query.filter_by(name=form.name.data.strip()).first()
        if existing:
            flash("A category with this name already exists.", "warning")
            return redirect(url_for("librarian_categories.category_list"))

        category = Category(
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None
        )
        db.session.add(category)
        db.session.commit()
        flash(f"Category '{category.name}' added.", "success")

    else:
        flash("Invalid category name.", "danger")

    return redirect(url_for("librarian_categories.category_list"))


@librarian_categories_bp.route("/categories/delete/<int:category_id>",
                                methods=["POST"])
@librarian_required
def delete_category(category_id: int):
    """
    Deletes a category.
    Books in this category will have their category set to NULL (SET NULL FK).
    """
    category = Category.query.get_or_404(category_id)
    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f"Category '{name}' deleted. Affected books are now uncategorized.", "info")
    return redirect(url_for("librarian_categories.category_list"))