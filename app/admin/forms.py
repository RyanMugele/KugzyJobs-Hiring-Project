from flask_wtf import FlaskForm

from wtforms import HiddenField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField

from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError


class PortfolioVerificationForm(FlaskForm):
    """Form for verifying portfolio submissions (FR-024, FR-025)."""

    decision = SelectField(
        "Verification Decision",
        choices=[
            ("", "Select decision"),
            ("approve", "Approve Portfolio"),
            ("reject", "Reject Portfolio"),
        ],
        validators=[DataRequired()],
    )

    notes = TextAreaField(
        "Admin Notes",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Add notes explaining the decision (required for rejections)...",
            "rows": 4,
        },
    )

    submit = SubmitField("Submit Decision")

    def validate_notes(self, field):
        """Require notes when rejecting a portfolio."""
        if self.decision.data == "reject" and not field.data.strip():
            raise ValidationError(
                "Notes are required when rejecting a portfolio."
            )


class UserSuspensionForm(FlaskForm):
    """Form for suspending user accounts (FR-056)."""

    reason = TextAreaField(
        "Suspension Reason",
        validators=[DataRequired(), Length(max=500)],
        render_kw={
            "placeholder": "Explain the reason for suspension...",
            "rows": 4,
        },
    )

    submit = SubmitField("Suspend User")


class ReportResolutionForm(FlaskForm):
    """Form for resolving user reports (FR-059)."""

    resolution = SelectField(
        "Resolution Decision",
        choices=[
            ("", "Select resolution"),
            ("resolved", "Issue Resolved - Action Taken"),
            ("dismissed", "Report Dismissed - No Action Needed"),
        ],
        validators=[DataRequired()],
    )

    admin_notes = TextAreaField(
        "Admin Notes",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={
            "placeholder": "Explain the action taken or why the report was dismissed...",
            "rows": 5,
        },
    )

    submit = SubmitField("Resolve Report")


class UserPasswordResetForm(FlaskForm):
    """Form for admin-initiated password resets (FR-057)."""

    confirmation = StringField(
        "Type 'RESET' to confirm",
        validators=[DataRequired()],
        render_kw={"placeholder": "Type RESET to confirm password reset"},
    )

    reason = TextAreaField(
        "Reason for Reset",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Optional reason for password reset...",
            "rows": 3,
        },
    )

    submit = SubmitField("Reset Password")

    def validate_confirmation(self, field):
        """Ensure admin types RESET to confirm action."""
        if field.data.upper() != "RESET":
            raise ValidationError(
                "You must type 'RESET' to confirm this action."
            )


class AdminSearchForm(FlaskForm):
    """Form for admin search functionality."""

    search_term = StringField(
        "Search",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Search users, portfolios, jobs..."},
    )

    search_type = SelectField(
        "Search In",
        choices=[
            ("users", "Users"),
            ("portfolios", "Portfolios"),
            ("jobs", "Jobs"),
            ("reports", "Reports"),
        ],
        default="users",
    )

    submit = SubmitField("Search")


class BulkActionForm(FlaskForm):
    """Form for bulk administrative actions."""

    selected_items = HiddenField()

    action = SelectField(
        "Bulk Action",
        choices=[
            ("", "Select action"),
            ("approve_portfolios", "Approve Selected Portfolios"),
            ("reject_portfolios", "Reject Selected Portfolios"),
            ("suspend_users", "Suspend Selected Users"),
            ("reactivate_users", "Reactivate Selected Users"),
        ],
        validators=[DataRequired()],
    )

    bulk_notes = TextAreaField(
        "Action Notes",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Add notes for this bulk action...",
            "rows": 3,
        },
    )

    submit = SubmitField("Execute Bulk Action")


class QuickModerationForm(FlaskForm):
    """Form for quick moderation actions on content."""

    content_type = HiddenField()
    content_id = HiddenField()

    action = SelectField(
        "Quick Action",
        choices=[
            ("", "Select action"),
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("remove", "Remove Content"),
            ("flag", "Flag for Review"),
        ],
        validators=[DataRequired()],
    )

    quick_note = StringField(
        "Quick Note",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Brief note about action..."},
    )

    submit = SubmitField("Execute")


class SystemMaintenanceForm(FlaskForm):
    """Form for system maintenance actions."""

    maintenance_type = SelectField(
        "Maintenance Action",
        choices=[
            ("", "Select maintenance action"),
            ("cleanup_tokens", "Cleanup Expired Reset Tokens"),
            ("update_ratings", "Recalculate User Ratings"),
            ("archive_old_jobs", "Archive Old Completed Jobs"),
            ("cleanup_reports", "Cleanup Resolved Reports"),
        ],
        validators=[DataRequired()],
    )

    confirmation = StringField(
        "Type 'CONFIRM' to proceed",
        validators=[DataRequired()],
        render_kw={"placeholder": "Type CONFIRM to execute maintenance"},
    )

    submit = SubmitField("Execute Maintenance")

    def validate_confirmation(self, field):
        """Ensure admin types CONFIRM to proceed with maintenance."""
        if field.data.upper() != "CONFIRM":
            raise ValidationError(
                "You must type 'CONFIRM' to proceed with maintenance."
            )


class AdminNoteForm(FlaskForm):
    """Form for adding administrative notes to users or content."""

    target_type = HiddenField()
    target_id = HiddenField()

    note_type = SelectField(
        "Note Type",
        choices=[
            ("", "Select note type"),
            ("warning", "Warning"),
            ("violation", "Policy Violation"),
            ("general", "General Note"),
            ("follow_up", "Follow-up Required"),
        ],
        validators=[DataRequired()],
    )

    note_content = TextAreaField(
        "Note Content",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={"placeholder": "Enter administrative note...", "rows": 5},
    )

    internal_only = SelectField(
        "Visibility",
        choices=[
            ("true", "Internal Only (Admin View)"),
            ("false", "Visible to User"),
        ],
        default="true",
    )

    submit = SubmitField("Add Note")


class UserVerificationForm(FlaskForm):
    """Form for manually verifying user accounts."""

    verification_type = SelectField(
        "Verification Type",
        choices=[
            ("", "Select verification type"),
            ("identity", "Identity Verification"),
            ("skills", "Skills Verification"),
            ("business", "Business Account Verification"),
        ],
        validators=[DataRequired()],
    )

    verification_notes = TextAreaField(
        "Verification Notes",
        validators=[DataRequired(), Length(max=500)],
        render_kw={
            "placeholder": "Document verification process and findings...",
            "rows": 4,
        },
    )

    verified_status = SelectField(
        "Verification Decision",
        choices=[
            ("", "Select decision"),
            ("verified", "Grant Verification"),
            ("rejected", "Reject Verification"),
            ("pending", "Require Additional Information"),
        ],
        validators=[DataRequired()],
    )

    submit = SubmitField("Update Verification Status")


class ContentFilterForm(FlaskForm):
    """Form for filtering content in admin views."""

    date_from = StringField(
        "From Date",
        validators=[Optional()],
        render_kw={"type": "date"},
    )

    date_to = StringField(
        "To Date",
        validators=[Optional()],
        render_kw={"type": "date"},
    )

    status_filter = SelectField(
        "Status",
        choices=[
            ("all", "All Statuses"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("active", "Active"),
            ("suspended", "Suspended"),
        ],
        default="all",
    )

    user_type_filter = SelectField(
        "User Type",
        choices=[
            ("all", "All User Types"),
            ("creator", "Creators"),
            ("editor", "Editors"),
            ("admin", "Administrators"),
        ],
        default="all",
    )

    priority_filter = SelectField(
        "Priority",
        choices=[
            ("all", "All Priorities"),
            ("high", "High Priority"),
            ("medium", "Medium Priority"),
            ("low", "Low Priority"),
        ],
        default="all",
    )

    submit = SubmitField("Apply Filters")


class AnnouncementForm(FlaskForm):
    """Form for creating platform announcements."""

    announcement_type = SelectField(
        "Announcement Type",
        choices=[
            ("", "Select type"),
            ("general", "General Announcement"),
            ("maintenance", "Maintenance Notice"),
            ("policy", "Policy Update"),
            ("feature", "New Feature"),
            ("urgent", "Urgent Notice"),
        ],
        validators=[DataRequired()],
    )

    title = StringField(
        "Announcement Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter announcement title..."},
    )

    content = TextAreaField(
        "Announcement Content",
        validators=[DataRequired(), Length(max=2000)],
        render_kw={"placeholder": "Enter announcement content...", "rows": 6},
    )

    target_audience = SelectField(
        "Target Audience",
        choices=[
            ("all", "All Users"),
            ("creators", "Content Creators Only"),
            ("editors", "Video Editors Only"),
            ("verified", "Verified Users Only"),
            ("new", "New Users Only"),
        ],
        default="all",
        validators=[DataRequired()],
    )

    priority = SelectField(
        "Priority Level",
        choices=[
            ("low", "Low Priority"),
            ("medium", "Medium Priority"),
            ("high", "High Priority"),
            ("urgent", "Urgent"),
        ],
        default="medium",
        validators=[DataRequired()],
    )

    expires_in_days = SelectField(
        "Expires In",
        choices=[
            ("7", "7 days"),
            ("14", "14 days"),
            ("30", "30 days"),
            ("60", "60 days"),
            ("never", "Never expires"),
        ],
        default="30",
    )

    submit = SubmitField("Create Announcement")
