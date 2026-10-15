from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SelectField
from wtforms import SubmitField
from wtforms import HiddenField
from wtforms import DecimalField
from wtforms import TextAreaField
from wtforms.validators import URL
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import NumberRange
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError


class ProfileUpdateForm(FlaskForm):
    """Form for updating editor profile (FR-018)."""

    fullName = StringField(
        "Full Name",
        validators=[DataRequired(), Length(max=255)],
        render_kw={"placeholder": "Enter your full name"},
    )

    specializations = TextAreaField(
        "Specializations",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "e.g., Color Grading, Motion Graphics, Sound Editing, YouTube Content, etc.",
            "rows": 3,
        },
    )

    experienceLevel = SelectField(
        "Experience Level",
        choices=[
            ("", "Select experience level"),
            ("beginner", "Beginner (0-1 years)"),
            ("intermediate", "Intermediate (2-4 years)"),
            ("advanced", "Advanced (5-7 years)"),
            ("expert", "Expert (8+ years)"),
        ],
        validators=[Optional()],
    )

    hourlyRate = DecimalField(
        "Hourly Rate (USD)",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )

    submit = SubmitField("Update Profile")


class PortfolioSubmissionForm(FlaskForm):
    """Form for submitting new portfolio items (FR-020, FR-021, FR-022)."""

    title = StringField(
        "Portfolio Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter a descriptive title for your work"},
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={
            "placeholder": "Describe your work, techniques used, and any special achievements...",
            "rows": 5,
        },
    )

    videoUrl = StringField(
        "Video URL",
        validators=[DataRequired(), URL(), Length(max=500)],
        render_kw={
            "placeholder": "https://youtube.com/watch?v=... or https://vimeo.com/..."
        },
    )

    skillTags = TextAreaField(
        "Skill Tags",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Enter skills demonstrated (e.g., Color Grading, Motion Graphics, Audio Sync)",
            "rows": 2,
        },
    )

    submit = SubmitField("Submit Portfolio")


class PortfolioEditForm(FlaskForm):
    """Form for editing portfolio items (FR-023)."""

    title = StringField(
        "Portfolio Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter a descriptive title for your work"},
    )

    description = TextAreaField(
        "Description",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={
            "placeholder": "Describe your work, techniques used, and any special achievements...",
            "rows": 5,
        },
    )

    videoUrl = StringField(
        "Video URL",
        validators=[DataRequired(), URL(), Length(max=500)],
        render_kw={
            "placeholder": "https://youtube.com/watch?v=... or https://vimeo.com/..."
        },
    )

    skillTags = TextAreaField(
        "Skill Tags",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Enter skills demonstrated (e.g., Color Grading, Motion Graphics, Audio Sync)",
            "rows": 2,
        },
    )

    submit = SubmitField("Update Portfolio")


class JobApplicationForm(FlaskForm):
    """Form for applying to jobs (FR-035, FR-036, FR-037)."""

    proposedRate = DecimalField(
        "Proposed Rate (USD)",
        validators=[DataRequired(), NumberRange(min=0.01)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )

    proposedTimeline = StringField(
        "Proposed Timeline",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., 3-5 business days, 1 week, etc."},
    )

    customProposal = TextAreaField(
        "Custom Proposal",
        validators=[DataRequired(), Length(max=1500)],
        render_kw={
            "placeholder": "Write your proposal here. Explain why you're the right fit, your approach, relevant experience, etc.",
            "rows": 8,
        },
    )

    submit = SubmitField("Submit Application")


class DeliverableUploadForm(FlaskForm):
    """Form for uploading project deliverables (FR-042)."""

    deliverableUrl = StringField(
        "Deliverable URL",
        validators=[DataRequired(), URL(), Length(max=500)],
        render_kw={
            "placeholder": "https://drive.google.com/... or https://dropbox.com/..."
        },
    )

    completionNotes = TextAreaField(
        "Completion Notes",
        validators=[Optional(), Length(max=500)],
        render_kw={
            "placeholder": "Add any notes about the completed work, special considerations, etc.",
            "rows": 4,
        },
    )

    submit = SubmitField("Upload Deliverable")


class MessageForm(FlaskForm):
    """Form for sending messages (FR-043, FR-044)."""

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
        render_kw={"placeholder": "Type your message here...", "rows": 6},
    )

    submit = SubmitField("Send Message")


class RatingForm(FlaskForm):
    """Form for submitting ratings (FR-051, FR-052)."""

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
            "placeholder": "Share your experience working with this creator...",
            "rows": 4,
        },
    )

    submit = SubmitField("Submit Rating")


class JobSearchForm(FlaskForm):
    """Form for searching and filtering jobs (FR-068, FR-069, FR-070)."""

    searchTerm = StringField(
        "Search Jobs",
        validators=[Optional(), Length(max=100)],
        render_kw={
            "placeholder": "Search by title, description, or keywords..."
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

    contentType = SelectField(
        "Content Type",
        choices=[
            ("", "Any content type"),
            ("YouTube Videos", "YouTube Videos"),
            ("Instagram Reels", "Instagram Reels"),
            ("TikTok Content", "TikTok Content"),
            ("Facebook Videos", "Facebook Videos"),
            ("Twitter Content", "Twitter Content"),
            ("LinkedIn Videos", "LinkedIn Videos"),
            ("Promotional Videos", "Promotional Videos"),
            ("Educational Content", "Educational Content"),
            ("Entertainment", "Entertainment"),
            ("Other", "Other"),
        ],
        validators=[Optional()],
    )

    skillFilter = StringField(
        "Required Skill",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., Color Grading, Motion Graphics"},
    )

    sortBy = SelectField(
        "Sort By",
        choices=[
            ("newest", "Newest First"),
            ("oldest", "Oldest First"),
            ("budget_high", "Highest Budget First"),
            ("budget_low", "Lowest Budget First"),
            ("deadline", "Deadline Approaching"),
        ],
        default="newest",
    )

    submit = SubmitField("Search Jobs")

    def validate_budgetMax(self, field):
        """Validates that maximum budget is greater than minimum budget."""
        if self.budgetMin.data and field.data:
            if field.data < self.budgetMin.data:
                raise ValidationError(
                    "Maximum budget must be greater than minimum budget."
                )


class ApplicationWithdrawalForm(FlaskForm):
    """Form for withdrawing job applications."""

    withdrawalReason = TextAreaField(
        "Reason for Withdrawal (Optional)",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Optionally explain why you're withdrawing this application...",
            "rows": 3,
        },
    )

    submit = SubmitField("Withdraw Application")


class QuickApplicationForm(FlaskForm):
    """Form for quick job applications with minimal fields."""

    jobId = HiddenField(validators=[DataRequired()])

    proposedRate = DecimalField(
        "Your Rate (USD)",
        validators=[DataRequired(), NumberRange(min=0.01)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
    )

    quickMessage = TextAreaField(
        "Quick Message",
        validators=[DataRequired(), Length(max=500)],
        render_kw={
            "placeholder": "Brief message about your interest and qualifications...",
            "rows": 4,
        },
    )

    submit = SubmitField("Quick Apply")


class PortfolioFilterForm(FlaskForm):
    """Form for filtering portfolio items."""

    status = SelectField(
        "Status",
        choices=[
            ("all", "All Portfolios"),
            ("pending", "Pending Verification"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="all",
    )

    skill = SelectField(
        "Skill Focus",
        choices=[
            ("", "All Skills"),
            ("Color Grading", "Color Grading"),
            ("Motion Graphics", "Motion Graphics"),
            ("Sound Editing", "Sound Editing"),
            ("Visual Effects", "Visual Effects"),
            ("Animation", "Animation"),
            ("Compositing", "Compositing"),
            ("Editing", "General Editing"),
            ("Other", "Other"),
        ],
        default="",
    )

    submit = SubmitField("Filter")


class ProjectCommunicationForm(FlaskForm):
    """Form for project-specific communication."""

    projectId = HiddenField(validators=[DataRequired()])

    messageType = SelectField(
        "Message Type",
        choices=[
            ("update", "Project Update"),
            ("question", "Question"),
            ("revision", "Revision Request"),
            ("completion", "Project Completion"),
            ("general", "General Message"),
        ],
        validators=[DataRequired()],
    )

    message = TextAreaField(
        "Message",
        validators=[DataRequired(), Length(max=1000)],
        render_kw={
            "placeholder": "Enter your project-related message...",
            "rows": 5,
        },
    )

    submit = SubmitField("Send Message")


class SkillsUpdateForm(FlaskForm):
    """Form for updating editor skills and specializations."""

    primarySkills = TextAreaField(
        "Primary Skills",
        validators=[DataRequired(), Length(max=300)],
        render_kw={
            "placeholder": "List your main skills (e.g., Video Editing, Color Correction, Audio Mixing)",
            "rows": 3,
        },
    )

    secondarySkills = TextAreaField(
        "Secondary Skills",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Additional skills you can offer (e.g., Graphic Design, Animation, Subtitling)",
            "rows": 3,
        },
    )

    software = TextAreaField(
        "Software Proficiency",
        validators=[Optional(), Length(max=300)],
        render_kw={
            "placeholder": "Software you're proficient in (e.g., Adobe Premiere, Final Cut Pro, DaVinci Resolve)",
            "rows": 2,
        },
    )

    submit = SubmitField("Update Skills")


class AvailabilityForm(FlaskForm):
    """Form for setting editor availability."""

    availability = SelectField(
        "Current Availability",
        choices=[
            ("available", "Available for New Projects"),
            ("busy", "Busy - Limited Availability"),
            ("unavailable", "Currently Unavailable"),
        ],
        validators=[DataRequired()],
    )

    workingHours = StringField(
        "Preferred Working Hours",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "e.g., 9 AM - 5 PM EST, Flexible, etc."},
    )

    maxProjects = SelectField(
        "Maximum Concurrent Projects",
        choices=[
            ("1", "1 project at a time"),
            ("2", "2 projects at a time"),
            ("3", "3 projects at a time"),
            ("4", "4 projects at a time"),
            ("5+", "5 or more projects"),
        ],
        default="2",
    )

    notes = TextAreaField(
        "Availability Notes",
        validators=[Optional(), Length(max=200)],
        render_kw={
            "placeholder": "Any additional notes about your availability...",
            "rows": 2,
        },
    )

    submit = SubmitField("Update Availability")
