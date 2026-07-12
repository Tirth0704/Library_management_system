from flask_wtf import FlaskForm
from wtforms import (
    StringField, DecimalField, IntegerField,
    SelectField, SubmitField, TextAreaField
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class AddBookForm(FlaskForm):
    """
    Librarian form to add a new book to the inventory.
    category_id choices are populated dynamically in the route.
    """
    title = StringField(
        "Book Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=255)
        ]
    )
    author = StringField(
        "Author",
        validators=[
            DataRequired(message="Author is required."),
            Length(max=150)
        ]
    )
    publisher = StringField(
        "Publisher",
        validators=[Optional(), Length(max=150)]
    )
    price = DecimalField(
        "Price (₹)",
        places=2,
        validators=[
            DataRequired(message="Price is required."),
            NumberRange(min=0.01, message="Price must be greater than 0.")
        ]
    )
    total_copies = IntegerField(
        "Total Copies",
        validators=[
            DataRequired(message="Total copies is required."),
            NumberRange(min=1, message="At least 1 copy required.")
        ]
    )
    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired(message="Please select a category.")]
    )
    submit = SubmitField("Add Book")


class EditBookForm(FlaskForm):
    """
    Librarian form to edit an existing book.
    Includes all fields from AddBookForm.
    """
    title = StringField(
        "Book Title",
        validators=[DataRequired(), Length(max=255)]
    )
    author = StringField(
        "Author",
        validators=[DataRequired(), Length(max=150)]
    )
    publisher = StringField(
        "Publisher",
        validators=[Optional(), Length(max=150)]
    )
    price = DecimalField(
        "Price (₹)",
        places=2,
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ]
    )
    total_copies = IntegerField(
        "Total Copies",
        validators=[DataRequired(), NumberRange(min=1)]
    )
    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Changes")


class AddCategoryForm(FlaskForm):
    """
    Librarian form to add a new book category.
    """
    name = StringField(
        "Category Name",
        validators=[
            DataRequired(message="Category name is required."),
            Length(max=100)
        ]
    )
    description = StringField(
        "Description (optional)",
        validators=[Optional(), Length(max=255)]
    )
    submit = SubmitField("Add Category")