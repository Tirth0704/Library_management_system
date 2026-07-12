from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Length


class RejectRequestForm(FlaskForm):
    """
    Librarian form to reject a book request.
    Rejection reason is mandatory and communicated to student.
    """
    rejection_reason = TextAreaField(
        "Rejection Reason",
        validators=[
            DataRequired(message="Please provide a reason for rejection."),
            Length(max=500)
        ]
    )
    submit = SubmitField("Reject Request")


class ApproveRequestForm(FlaskForm):
    """
    Librarian form to approve a book request.
    Issue date is the actual date of physical handover.
    """
    issue_date = DateField(
        "Issue Date",
        validators=[DataRequired(message="Issue date is required.")]
    )
    submit = SubmitField("Approve & Issue")