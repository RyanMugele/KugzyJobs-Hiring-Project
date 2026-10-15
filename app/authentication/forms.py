from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import BooleanField
from wtforms import PasswordField
from wtforms import ValidationError
from wtforms import TextAreaField
from wtforms import SelectField

from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import EqualTo
from wtforms.validators import Optional
from wtforms.validators import DataRequired

from app import db
from ..models.user import User


def validate_unique_email(form, field):
    """
    Validator to ensure that the email address is unique across all user types.

    Raises a generic ValidationError if the email is already used.
    """
    email_address = field.data.strip().lower()  # Normalize input

    # Check for email existence in User table (covers all user types)
    email_exists = (
        db.session.query(User.emailAddress)
        .filter(User.emailAddress.ilike(email_address))
        .first()
    )
    if email_exists:
        raise ValidationError("This email address is already registered.")


class LoginForm(FlaskForm):
    emailAddress = StringField(
        "Enter your email address",
        validators=[DataRequired(), Length(1, 128), Email()],
        render_kw={"placeholder": "Enter email address here"},
    )
    password = PasswordField(
        "Enter your password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter password here"},
    )
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class PasswordResetRequestForm(FlaskForm):
    emailAddress = StringField(
        "Enter your email address",
        validators=[DataRequired(), Length(1, 128), Email()],
        render_kw={"placeholder": "Enter your email address"},
    )
    submit = SubmitField("Send Reset Link")


class PasswordResetForm(FlaskForm):
    password = PasswordField(
        "Enter your new password",
        validators=[
            DataRequired(),
            Length(
                min=8, message="Password must be at least 8 characters long"
            ),
        ],
        render_kw={
            "autocomplete": "new-password",
            "placeholder": "Enter new password",
        },
    )
    confirmPassword = PasswordField(
        "Confirm your password",
        validators=[DataRequired(), EqualTo("password")],
        render_kw={
            "autocomplete": "new-password",
            "placeholder": "Re-enter new password",
        },
    )
    submit = SubmitField("Reset Password")


class BaseUserForm(FlaskForm):
    fullName = StringField(
        "Full Name",
        validators=[DataRequired(), Length(max=255)],
        render_kw={"placeholder": "Enter your full name"},
    )
    emailAddress = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Length(max=255),
            Email(),
            validate_unique_email,
        ],
        render_kw={"placeholder": "Enter your email address"},
    )
    password = PasswordField(
        "Create a password",
        validators=[
            DataRequired(),
            Length(
                min=8, message="Password must be at least 8 characters long"
            ),
        ],
        render_kw={
            "autocomplete": "new-password",
            "placeholder": "Create a strong password",
        },
    )
    confirmPassword = PasswordField(
        "Confirm your password",
        validators=[DataRequired(), EqualTo("password")],
        render_kw={
            "autocomplete": "new-password",
            "placeholder": "Re-enter your password",
        },
    )
    consent = BooleanField(
        "I agree to the Terms and Conditions",
        validators=[DataRequired()],
    )

    submit = SubmitField("Sign Up")


class CreatorRegistrationForm(BaseUserForm):
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


class EditorRegistrationForm(BaseUserForm):
    specializations = TextAreaField(
        "Specializations",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "List your video editing skills (e.g., Video Editing, Color Grading, Motion Graphics)",
            "rows": 3,
        },
    )
    experienceLevel = SelectField(
        "Experience Level",
        choices=[
            ("", "Select experience level"),
            ("beginner", "Beginner (0-1 years)"),
            ("intermediate", "Intermediate (1-3 years)"),
            ("advanced", "Advanced (3-5 years)"),
            ("expert", "Expert (5+ years)"),
        ],
        validators=[Optional()],
    )
    hourlyRate = StringField(
        "Hourly Rate (USD)",
        validators=[Optional()],
        render_kw={"placeholder": "Enter your hourly rate (optional)"},
    )


class AdminRegistrationForm(BaseUserForm):
    roleDesignation = SelectField(
        "Role Designation",
        choices=[
            ("", "Select admin role"),
            ("moderator", "Content Moderator"),
            ("super_admin", "Super Administrator"),
            ("support", "Customer Support"),
        ],
        validators=[Optional()],
        default="moderator",
    )
    adminCode = StringField(
        "Admin Registration Code",
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter admin registration code"},
    )

    def validate_adminCode(self, field):
        """
        Validates the admin registration code.
        """
        # This should match a code from your configuration
        from flask import current_app

        valid_code = current_app.config.get(
            "ADMIN_REGISTRATION_CODE", "ADMIN2025"
        )
        if field.data != valid_code:
            raise ValidationError("Invalid admin registration code.")
