from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length


class RecommendationForm(FlaskForm):
    """
    Student form to submit a book recommendation.

    book_name and author are required.
    publisher and reason are optional as per spec.
    """
    book_name = StringField(
        "Book Name",
        validators=[
            DataRequired(message="Book name is required."),
            Length(max=255)
        ]
    )
    author = StringField(
        "Author",
        validators=[
            DataRequired(message="Author name is required."),
            Length(max=150)
        ]
    )
    publisher = StringField(
        "Publisher (optional)",
        validators=[Optional(), Length(max=150)]
    )
    reason = TextAreaField(
        "Why should we add this book? (optional)",
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField("Submit Recommendation")