from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField,
    SubmitField, SelectField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.utils.validators import (
    validate_password_strength,
    validate_phone_number,
    validate_enrollment_number,
)


class LoginForm(FlaskForm):
    """
    Shared login form for both students and librarian.
    Role is determined after credential verification.
    """
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address.")
        ]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required.")
        ]
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    """
    Student self-registration form.
    No approval needed — account is active immediately.
    """
    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=3, max=150, message="Name must be 3–150 characters.")
        ]
    )
    enrollment_number = StringField(
        "Enrollment Number",
        validators=[
            DataRequired(message="Enrollment number is required."),
            validate_enrollment_number
        ]
    )
    email = StringField(
        "Email Address",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Enter a valid email address.")
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
            ("", "Select Department"),
            ("Computer Science", "Computer Science"),
            ("Information Technology", "Information Technology"),
            ("Electronics", "Electronics"),
            ("Mechanical", "Mechanical"),
            ("Civil", "Civil"),
            ("Electrical", "Electrical"),
            ("Chemical", "Chemical"),
            ("Other", "Other"),
        ],
        validators=[DataRequired(message="Please select a department.")]
    )
    semester = SelectField(
        "Semester",
        choices=[
            ("", "Select Semester"),
            ("Semester 1", "Semester 1"),
            ("Semester 2", "Semester 2"),
            ("Semester 3", "Semester 3"),
            ("Semester 4", "Semester 4"),
            ("Semester 5", "Semester 5"),
            ("Semester 6", "Semester 6"),
            ("Semester 7", "Semester 7"),
            ("Semester 8", "Semester 8"),
        ],
        validators=[DataRequired(message="Please select a semester.")]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            validate_password_strength
        ]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords do not match.")
        ]
    )
    submit = SubmitField("Create Account")