from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from app.utils.validators import validate_phone_number


class EditProfileForm(FlaskForm):
    """
    Student can update their own profile.
    Email and enrollment number are not editable post-registration.
    Semester can be updated each term.
    """
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=3, max=150)
        ]
    )
    phone_number = StringField(
        "Phone / WhatsApp Number",
        validators=[
            DataRequired(message="Phone number is required."),
            validate_phone_number
        ]
    )
    department = SelectField(
        "Department",
        choices=[
            ("Computer Science", "Computer Science"),
            ("Information Technology", "Information Technology"),
            ("Electronics", "Electronics"),
            ("Mechanical", "Mechanical"),
            ("Civil", "Civil"),
            ("Electrical", "Electrical"),
            ("Chemical", "Chemical"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()]
    )
    semester = SelectField(
        "Semester",
        choices=[
            ("Semester 1", "Semester 1"),
            ("Semester 2", "Semester 2"),
            ("Semester 3", "Semester 3"),
            ("Semester 4", "Semester 4"),
            ("Semester 5", "Semester 5"),
            ("Semester 6", "Semester 6"),
            ("Semester 7", "Semester 7"),
            ("Semester 8", "Semester 8"),
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField("Save Changes")