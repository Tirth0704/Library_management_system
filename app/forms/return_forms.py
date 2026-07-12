from flask_wtf import FlaskForm
from wtforms import (
    SelectField, DecimalField, TextAreaField,
    BooleanField, SubmitField
)
from wtforms.validators import DataRequired, Optional, NumberRange


class ProcessReturnForm(FlaskForm):
    """
    Librarian form to process a book return.

    condition:
        Good    → No extra charge
        Damaged → Librarian enters damage_fine
        Lost    → Full book price charged, no rent

    damage_fine is only relevant when condition = Damaged.
    is_lost overrides everything and charges full price.
    """
    condition = SelectField(
        "Book Condition",
        choices=[
            ("Good", "Good — No Damage"),
            ("Damaged", "Damaged — Charge Damage Fine"),
            ("Lost", "Lost — Charge Full Price"),
        ],
        validators=[DataRequired()]
    )
    damage_fine = DecimalField(
        "Damage Fine Amount (₹)",
        places=2,
        validators=[
            Optional(),
            NumberRange(min=0, message="Damage fine cannot be negative.")
        ],
        default=0.00
    )
    librarian_notes = TextAreaField(
        "Librarian Notes (optional)",
        validators=[Optional()]
    )
    submit = SubmitField("Process Return")