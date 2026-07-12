import re
from wtforms.validators import ValidationError


def validate_phone_number(form, field):
    """
    WTForms validator for Indian phone numbers.
    Accepts 10-digit numbers, optionally prefixed with +91 or 0.

    Usage in WTForms:
        phone = StringField('Phone', validators=[validate_phone_number])
    """
    raw = field.data.strip().replace(" ", "").replace("-", "")

    # Strip country code if present
    if raw.startswith("+91"):
        raw = raw[3:]
    elif raw.startswith("91") and len(raw) == 12:
        raw = raw[2:]
    elif raw.startswith("0") and len(raw) == 11:
        raw = raw[1:]

    if not re.fullmatch(r"[6-9]\d{9}", raw):
        raise ValidationError(
            "Enter a valid 10-digit Indian mobile number."
        )

    # Normalize to 10 digits
    field.data = raw


def validate_enrollment_number(form, field):
    """
    Enrollment number must be alphanumeric and 5–20 characters.
    Allows uppercase, lowercase, digits, and hyphens.
    """
    value = field.data.strip()
    if not re.fullmatch(r"[A-Za-z0-9\-]{5,20}", value):
        raise ValidationError(
            "Enrollment number must be 5–20 alphanumeric characters."
        )


def validate_positive_amount(form, field):
    """
    Validates that a decimal field is a positive non-zero number.
    Used for damage fine amounts entered by librarian.
    """
    try:
        amount = float(field.data)
        if amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
    except (TypeError, ValueError):
        raise ValidationError("Enter a valid amount.")


def validate_password_strength(form, field):
    """
    Password must be at least 8 characters.
    Must contain at least one letter and one digit.
    """
    password = field.data

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("Password must contain at least one letter.")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit.")