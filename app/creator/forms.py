from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms import DecimalField
from wtforms import DateField
from wtforms import HiddenField

from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange
from wtforms.validators import ValidationError

from datetime import datetime
from datetime import timedelta


class ProfileUpdateForm(FlaskForm):
    fullName = StringField(
        "Full Name",
        validators=[DataRequired(), Length(max=255)],
        render_kw={"placeholder": "Enter your full name"},
    )
    contentType = StringField(
        "Content Type",
        validators=[Optional(), Length(max=100)],
        render_kw={
            "placeholder": "e.g., YouTube Videos, Instagram Reels, TikTok Content"
        },
    )
    platformFocus = SelectField(
        "Platform Focus",
        choices=[
            ("", "Select primary platform"),
            ("YouTube", "YouTube"),
            ("Instagram", "Instagram"),
            ("TikTok", "TikTok"),
            ("Facebook", "Facebook"),
            ("Twitter", "Twitter"),
            ("LinkedIn", "LinkedIn"),
            ("Other", "Other"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Update Profile")


class JobPostingForm(FlaskForm):
    title = StringField(
        "Job Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter a descriptive job title"},
    )
    description = TextAreaField(
        "Job Description",
        validators=[DataRequired(), Length(max=2000)],
        render_kw={
            "placeholder": "Describe the project requirements, style, and expectations...",
            "rows": 6,
        },
    )
    budgetMin = DecimalField(
        "Minimum Budget (USD)",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )
    budgetMax = DecimalField(
        "Maximum Budget (USD)",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )
    deadline = DateField(
        "Project Deadline",
        validators=[Optional()],
        default=datetime.utcnow() + timedelta(days=30),
    )
    requiredSkills = TextAreaField(
        "Required Skills",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "List required skills (e.g., Video Editing, Color Grading, Motion Graphics)",
            "rows": 3,
        },
    )
    submit = SubmitField("Post Job")

    def validate_budgetMax(self, field):
        """
        Validates that maximum budget is greater than minimum budget.
        """
        if self.budgetMin.data and field.data:
            if field.data < self.budgetMin.data:
                raise ValidationError(
                    "Maximum budget must be greater than minimum budget."
                )

    def validate_deadline(self, field):
        """
        Validates that deadline is in the future.
        """
        if field.data and field.data <= datetime.utcnow().date():
            raise ValidationError("Deadline must be in the future.")


class JobUpdateForm(JobPostingForm):
    submit = SubmitField("Update Job")


class EditorSelectionForm(FlaskForm):
    selectedEditorId = HiddenField(validators=[DataRequired()])
    selectionNotes = TextAreaField(
        "Selection Notes (Optional)",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Add any notes about why you selected this editor...",
            "rows": 3,
        },
    )
    submit = SubmitField("Select Editor")


class JobCompletionForm(FlaskForm):
    deliverableUrl = StringField(
        "Deliverable URL",
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Enter URL to completed work (if available)"},
    )
    completionNotes = TextAreaField(
        "Completion Notes",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Add any final notes about the project...",
            "rows": 3,
        },
    )
    submit = SubmitField("Mark as Completed")


class MessageForm(FlaskForm):
    receiverId = HiddenField(validators=[DataRequired()])
    jobId = HiddenField()
    subject = StringField(
        "Subject",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Enter message subject"},
    )
    messageContent = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={"placeholder": "Type your message here...", "rows": 5},
    )
    submit = SubmitField("Send Message")


class RatingForm(FlaskForm):
    jobId = HiddenField(validators=[DataRequired()])
    rateeId = HiddenField(validators=[DataRequired()])
    ratingValue = SelectField(
        "Rating",
        choices=[
            ("5", "5 Stars - Excellent"),
            ("4", "4 Stars - Good"),
            ("3", "3 Stars - Average"),
            ("2", "2 Stars - Poor"),
            ("1", "1 Star - Terrible"),
        ],
        validators=[DataRequired()],
        coerce=int,
        default="3",
    )
    reviewText = TextAreaField(
        "Review (Optional)",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Share your experience working with this editor...",
            "rows": 4,
        },
    )
    submit = SubmitField("Submit Rating")


class PaymentInitiationForm(FlaskForm):
    jobId = HiddenField(validators=[DataRequired()])
    agreedAmount = DecimalField(
        "Payment Amount (USD)",
        validators=[DataRequired(), NumberRange(min=0.01)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )
    paymentMethod = SelectField(
        "Payment Method",
        choices=[
            ("", "Select payment method"),
            ("pesapal", "Pesapal"),
            ("mpesa", "M-Pesa"),
            ("bank_transfer", "Bank Transfer"),
            ("other", "Other"),
        ],
        validators=[DataRequired()],
        default="pesapal",
    )
    paymentNotes = TextAreaField(
        "Payment Notes (Optional)",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Add any payment-related notes...",
            "rows": 3,
        },
    )
    submit = SubmitField("Initiate Payment")


class EditorSearchForm(FlaskForm):
    searchTerm = StringField(
        "Search Editors",
        validators=[Optional(), Length(max=100)],
        render_kw={
            "placeholder": "Search by name, skills, or specialization..."
        },
    )
    experienceLevel = SelectField(
        "Experience Level",
        choices=[
            ("", "Any experience level"),
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
            ("expert", "Expert"),
        ],
        validators=[Optional()],
    )
    maxBudget = DecimalField(
        "Max Hourly Rate (USD)",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )
    skillFilter = StringField(
        "Required Skill",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., Color Grading, Motion Graphics"},
    )
    verifiedOnly = SelectField(
        "Verification Status",
        choices=[
            ("", "All editors"),
            ("verified", "Verified editors only"),
            ("unverified", "Unverified editors only"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Search")


class PaymentConfirmationForm(FlaskForm):
    paymentId = HiddenField(validators=[DataRequired()])
    confirmPayment = SubmitField("Confirm Payment Completion")


class ReportForm(FlaskForm):
    reportedUserId = HiddenField()
    reportedPortfolioId = HiddenField()
    reportReason = TextAreaField(
        "Report Reason",
        validators=[DataRequired(), Length(max=500)],
        render_kw={
            "placeholder": "Please describe the issue in detail...",
            "rows": 4,
        },
    )
    submit = SubmitField("Submit Report")
