import flask

from flask_login import current_user
from flask_login import login_required

from decimal import Decimal
from datetime import datetime

from . import editor
from .forms import JobSearchForm
from .forms import MessageForm
from .forms import RatingForm
from .forms import JobApplicationForm
from .forms import PortfolioEditForm
from .forms import ProfileUpdateForm
from .forms import DeliverableUploadForm
from .forms import PortfolioSubmissionForm

from app import db

from ..models import Job
from ..models import Rating
from ..models import Message
from ..models import Portfolio
from ..models import JobApplication


def editor_required(f):
    """Decorator to ensure user is an editor."""

    def decorated_function(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or current_user.userType != "editor"
        ):
            flask.flash("Access denied. Editor account required.", "danger")
            return flask.redirect(flask.url_for("authentication.login"))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@editor.route("/dashboard")
@login_required
@editor_required
def dashboard():
    """Display editor dashboard with overview of jobs, applications, and portfolio status."""
    editor_data = current_user.getSpecificUserData()

    # Get dashboard statistics
    total_applications = len(editor_data.jobApplications)
    active_applications = len(editor_data.getActiveApplications())
    current_jobs = editor_data.getCurrentJobs()
    completed_jobs = editor_data.getCompletedJobs()

    # Get portfolio statistics
    total_portfolios = len(editor_data.portfolios)
    verified_portfolios = len(editor_data.getVerifiedPortfolios())
    pending_portfolios = len(editor_data.getPendingPortfolios())

    # Get recent activity
    recent_jobs = Job.getPostedJobs()[:5]
    recent_messages = Message.getMessagesForUser(
        current_user.userId, "received"
    )[:5]

    dashboard_data = {
        "verification_status": editor_data.isVerified,
        "total_applications": total_applications,
        "active_applications": active_applications,
        "current_jobs": len(current_jobs),
        "completed_jobs": len(completed_jobs),
        "total_portfolios": total_portfolios,
        "verified_portfolios": verified_portfolios,
        "pending_portfolios": pending_portfolios,
        "recent_jobs": recent_jobs,
        "recent_messages": recent_messages,
        "current_jobs_list": current_jobs,
        "average_rating": float(current_user.averageRating)
        if current_user.averageRating
        else 0,
        "total_ratings": current_user.totalRatings,
    }

    return flask.render_template("editor/dashboard.html", data=dashboard_data)


@editor.route("/profile", methods=["GET", "POST"])
@login_required
@editor_required
def profile():
    """Display and update editor profile (FR-018)."""
    editor_data = current_user.getSpecificUserData()
    form = ProfileUpdateForm()

    if flask.request.method == "GET":
        form.fullName.data = current_user.fullName
        form.specializations.data = editor_data.specializations
        form.experienceLevel.data = editor_data.experienceLevel
        form.hourlyRate.data = editor_data.hourlyRate

    if form.validate_on_submit():
        try:
            # Update user data
            current_user.fullName = form.fullName.data

            # Update editor-specific data
            editor_data.updateSpecializationsAndRates(
                specializations=form.specializations.data,
                experienceLevel=form.experienceLevel.data,
                hourlyRate=float(form.hourlyRate.data)
                if form.hourlyRate.data
                else None,
            )

            db.session.commit()
            flask.flash("Profile updated successfully!", "success")
            return flask.redirect(flask.url_for("editor.profile"))

        except Exception:
            db.session.rollback()
            flask.flash("Failed to update profile. Please try again.", "danger")

    return flask.render_template(
        "editor/profile.html", form=form, editor=editor_data
    )


# ------------------------------------------------------------------------------
#                           PORTFOLIO MANAGEMENT (FR-020 to FR-023)
# ------------------------------------------------------------------------------
@editor.route("/portfolio")
@login_required
@editor_required
def portfolio():
    """Display editor's portfolio items."""
    editor_data = current_user.getSpecificUserData()

    status_filter = flask.request.args.get("status", "all")

    if status_filter == "approved":
        portfolios = editor_data.getVerifiedPortfolios()
    elif status_filter == "pending":
        portfolios = editor_data.getPendingPortfolios()
    elif status_filter == "rejected":
        portfolios = [
            p
            for p in editor_data.portfolios
            if p.verificationStatus == "rejected"
        ]
    else:
        portfolios = editor_data.portfolios

    portfolios.sort(key=lambda x: x.dateCreated, reverse=True)

    return flask.render_template(
        "editor/portfolio.html",
        portfolios=portfolios,
        status_filter=status_filter,
        verification_status=editor_data.isVerified,
    )


@editor.route("/portfolio/new", methods=["GET", "POST"])
@login_required
@editor_required
def new_portfolio():
    """Submit new portfolio item (FR-020, FR-021, FR-022)."""
    form = PortfolioSubmissionForm()

    if form.validate_on_submit():
        try:
            editor_data = current_user.getSpecificUserData()

            portfolio_details = {
                "title": form.title.data,
                "description": form.description.data,
                "videoUrl": form.videoUrl.data,
                "skillTags": form.skillTags.data,
            }

            portfolio = editor_data.addPortfolioItem(portfolio_details)
            flask.flash("Portfolio item submitted for verification!", "success")
            return flask.redirect(
                flask.url_for(
                    "editor.portfolio_detail",
                    portfolio_id=portfolio.portfolioId,
                )
            )

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to submit portfolio item. Please try again.", "danger"
            )

    return flask.render_template("editor/new_portfolio.html", form=form)


@editor.route("/portfolio/<int:portfolio_id>")
@login_required
@editor_required
def portfolio_detail(portfolio_id):
    """View detailed portfolio item."""
    editor_data = current_user.getSpecificUserData()
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    # Ensure this portfolio belongs to the current editor
    if portfolio.editorId != editor_data.editorId:
        flask.flash(
            "Access denied. You can only view your own portfolio items.",
            "danger",
        )
        return flask.redirect(flask.url_for("editor.portfolio"))

    return flask.render_template(
        "editor/portfolio_detail.html", portfolio=portfolio
    )


@editor.route("/portfolio/<int:portfolio_id>/edit", methods=["GET", "POST"])
@login_required
@editor_required
def edit_portfolio(portfolio_id):
    """Edit portfolio item (FR-023) - only pending or rejected items."""
    editor_data = current_user.getSpecificUserData()
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    if portfolio.editorId != editor_data.editorId:
        flask.flash(
            "Access denied. You can only edit your own portfolio items.",
            "danger",
        )
        return flask.redirect(flask.url_for("editor.portfolio"))

    if portfolio.verificationStatus == "approved":
        flask.flash("Cannot edit approved portfolio items.", "warning")
        return flask.redirect(
            flask.url_for("editor.portfolio_detail", portfolio_id=portfolio_id)
        )

    form = PortfolioEditForm()

    if flask.request.method == "GET":
        form.title.data = portfolio.title
        form.description.data = portfolio.description
        form.videoUrl.data = portfolio.videoUrl
        form.skillTags.data = portfolio.skillTags

    if form.validate_on_submit():
        try:
            portfolio.updatePortfolioDetails(
                title=form.title.data,
                description=form.description.data,
                skillTags=form.skillTags.data,
            )

            if form.videoUrl.data != portfolio.videoUrl:
                portfolio.uploadVideoFile(form.videoUrl.data)

            # Resubmit for verification if it was rejected
            if portfolio.verificationStatus == "rejected":
                portfolio.submitForVerification()

            flask.flash("Portfolio item updated successfully!", "success")
            return flask.redirect(
                flask.url_for(
                    "editor.portfolio_detail", portfolio_id=portfolio_id
                )
            )

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to update portfolio item. Please try again.", "danger"
            )

    return flask.render_template(
        "editor/edit_portfolio.html", form=form, portfolio=portfolio
    )


@editor.route("/portfolio/<int:portfolio_id>/delete", methods=["POST"])
@login_required
@editor_required
def delete_portfolio(portfolio_id):
    """Delete portfolio item (FR-023)."""
    editor_data = current_user.getSpecificUserData()
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    if portfolio.editorId != editor_data.editorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("editor.portfolio"))

    try:
        db.session.delete(portfolio)
        db.session.commit()
        flask.flash("Portfolio item deleted successfully.", "success")
    except Exception:
        db.session.rollback()
        flask.flash("Failed to delete portfolio item.", "danger")

    return flask.redirect(flask.url_for("editor.portfolio"))


# ------------------------------------------------------------------------------
#                              JOB DISCOVERY (FR-068 to FR-070)
# ------------------------------------------------------------------------------
@editor.route("/jobs")
@login_required
@editor_required
def jobs():
    """Browse available jobs (FR-068, FR-069, FR-070)."""
    form = JobSearchForm()
    jobs_list = []

    if flask.request.method == "GET" and flask.request.args:
        # Handle search and filter parameters
        budget_min = flask.request.args.get("budgetMin")
        budget_max = flask.request.args.get("budgetMax")
        content_type = flask.request.args.get("contentType", "").strip()
        skill_filter = flask.request.args.get("skillFilter", "").strip()
        search_term = flask.request.args.get("searchTerm", "").strip()

        # Start with posted jobs only
        query = Job.query.filter_by(status="posted")

        # Apply budget filters
        if budget_min:
            try:
                min_budget = float(budget_min)
                query = query.filter(Job.budgetMin >= min_budget)
            except ValueError:
                pass

        if budget_max:
            try:
                max_budget = float(budget_max)
                query = query.filter(Job.budgetMax <= max_budget)
            except ValueError:
                pass

        # Filter by content type or skills
        if content_type:
            query = query.join(Job.creator).filter(
                Job.creator.has(contentType=content_type)
            )

        if skill_filter:
            query = query.filter(Job.requiredSkills.like(f"%{skill_filter}%"))

        # Search in title and description
        if search_term:
            query = query.filter(
                (Job.title.like(f"%{search_term}%"))
                | (Job.description.like(f"%{search_term}%"))
            )

        jobs_list = query.order_by(Job.dateCreated.desc()).all()

        # Pre-populate form
        form.budgetMin.data = Decimal(budget_min) if budget_min else None
        form.budgetMax.data = Decimal(budget_max) if budget_max else None
        form.contentType.data = content_type
        form.skillFilter.data = skill_filter
        form.searchTerm.data = search_term

    else:
        # Default: show all posted jobs
        jobs_list = Job.getPostedJobs()

    # Check which jobs the editor has already applied to
    editor_data = current_user.getSpecificUserData()
    applied_job_ids = {app.jobId for app in editor_data.jobApplications}

    return flask.render_template(
        "editor/jobs.html",
        jobs=jobs_list,
        form=form,
        applied_job_ids=applied_job_ids,
    )


@editor.route("/jobs/<int:job_id>")
@login_required
@editor_required
def job_detail(job_id):
    """View detailed job information."""
    job = Job.query.get_or_404(job_id)
    editor_data = current_user.getSpecificUserData()

    # Check if editor has already applied
    existing_application = JobApplication.checkExistingApplication(
        job_id, editor_data.editorId
    )

    # Get other applications count (without showing details)
    application_count = len(job.applications)

    job_info = {
        "job": job,
        "existing_application": existing_application,
        "can_apply": job.status == "posted" and not existing_application,
        "application_count": application_count,
        "budget_range": job.getBudgetRange(),
        "required_skills": job.getRequiredSkillsList(),
        "days_posted": (datetime.now() - job.dateCreated).days,
    }

    return flask.render_template("editor/job_detail.html", data=job_info)


# ------------------------------------------------------------------------------
#                           JOB APPLICATIONS (FR-035 to FR-037)
# ------------------------------------------------------------------------------
@editor.route("/applications")
@login_required
@editor_required
def applications():
    """View editor's job applications."""
    editor_data = current_user.getSpecificUserData()

    status_filter = flask.request.args.get("status", "all")

    if status_filter == "pending":
        applications_list = editor_data.getActiveApplications()
    elif status_filter == "accepted":
        applications_list = editor_data.getAcceptedApplications()
    elif status_filter == "declined":
        applications_list = [
            app
            for app in editor_data.jobApplications
            if app.status == "declined"
        ]
    else:
        applications_list = editor_data.jobApplications

    applications_list.sort(key=lambda x: x.dateCreated, reverse=True)

    return flask.render_template(
        "editor/applications.html",
        applications=applications_list,
        status_filter=status_filter,
    )


@editor.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
@login_required
@editor_required
def apply_for_job(job_id):
    """Apply for a job (FR-035, FR-036, FR-037)."""
    job = Job.query.get_or_404(job_id)
    editor_data = current_user.getSpecificUserData()

    # Check if editor can apply
    if job.status != "posted":
        flask.flash("This job is no longer accepting applications.", "warning")
        return flask.redirect(flask.url_for("editor.job_detail", job_id=job_id))

    # Check if already applied
    existing_application = JobApplication.checkExistingApplication(
        job_id, editor_data.editorId
    )
    if existing_application:
        flask.flash("You have already applied for this job.", "warning")
        return flask.redirect(flask.url_for("editor.job_detail", job_id=job_id))

    form = JobApplicationForm()

    # Pre-populate with editor's hourly rate if available
    if flask.request.method == "GET" and editor_data.hourlyRate:
        form.proposedRate.data = editor_data.hourlyRate

    if form.validate_on_submit():
        try:
            application_details = {
                "proposedRate": float(form.proposedRate.data),
                "proposedTimeline": form.proposedTimeline.data,
                "customProposal": form.customProposal.data,
            }

            application = editor_data.applyForJob(job_id, application_details)
            flask.flash("Application submitted successfully!", "success")
            return flask.redirect(
                flask.url_for(
                    "editor.application_detail",
                    application_id=application.jobApplicationId,
                )
            )

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to submit application. Please try again.", "danger"
            )

    return flask.render_template(
        "editor/apply_for_job.html", job=job, form=form
    )


@editor.route("/applications/<int:application_id>")
@login_required
@editor_required
def application_detail(application_id):
    """View detailed application information."""
    editor_data = current_user.getSpecificUserData()
    application = JobApplication.query.get_or_404(application_id)

    if application.editorId != editor_data.editorId:
        flask.flash(
            "Access denied. You can only view your own applications.", "danger"
        )
        return flask.redirect(flask.url_for("editor.applications"))

    application_info = {
        "application": application,
        "job": application.job,
        "proposal_summary": application.getProposalSummary(),
        "budget_comparison": application.compareWithJobBudget(),
        "can_edit": application.isEditable(),
    }

    return flask.render_template(
        "editor/application_detail.html", data=application_info
    )


@editor.route(
    "/applications/<int:application_id>/edit", methods=["GET", "POST"]
)
@login_required
@editor_required
def edit_application(application_id):
    """Edit pending job application."""
    editor_data = current_user.getSpecificUserData()
    application = JobApplication.query.get_or_404(application_id)

    if application.editorId != editor_data.editorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("editor.applications"))

    if not application.isEditable():
        flask.flash("Cannot edit this application.", "warning")
        return flask.redirect(
            flask.url_for(
                "editor.application_detail", application_id=application_id
            )
        )

    form = JobApplicationForm()

    if flask.request.method == "GET":
        form.proposedRate.data = application.proposedRate
        form.proposedTimeline.data = application.proposedTimeline
        form.customProposal.data = application.customProposal

    if form.validate_on_submit():
        try:
            success = application.updateProposal(
                proposedRate=float(form.proposedRate.data),
                proposedTimeline=form.proposedTimeline.data,
                customProposal=form.customProposal.data,
            )

            if success:
                flask.flash("Application updated successfully!", "success")
                return flask.redirect(
                    flask.url_for(
                        "editor.application_detail",
                        application_id=application_id,
                    )
                )
            else:
                flask.flash("Cannot edit this application.", "warning")

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to update application. Please try again.", "danger"
            )

    return flask.render_template(
        "editor/edit_application.html", application=application, form=form
    )


@editor.route("/applications/<int:application_id>/withdraw", methods=["POST"])
@login_required
@editor_required
def withdraw_application(application_id):
    """Withdraw pending job application."""
    editor_data = current_user.getSpecificUserData()
    application = JobApplication.query.get_or_404(application_id)

    if application.editorId != editor_data.editorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("editor.applications"))

    try:
        success = application.withdrawApplication()
        if success:
            flask.flash("Application withdrawn successfully.", "success")
        else:
            flask.flash("Cannot withdraw this application.", "warning")
    except Exception:
        db.session.rollback()
        flask.flash("Failed to withdraw application.", "danger")

    return flask.redirect(flask.url_for("editor.applications"))


# ------------------------------------------------------------------------------
#                              PROJECT WORK (FR-042)
# ------------------------------------------------------------------------------
@editor.route("/projects")
@login_required
@editor_required
def projects():
    """View current and completed projects."""
    editor_data = current_user.getSpecificUserData()

    current_jobs = editor_data.getCurrentJobs()
    completed_jobs = editor_data.getCompletedJobs()

    projects_data = {
        "current_jobs": current_jobs,
        "completed_jobs": completed_jobs,
        "total_current": len(current_jobs),
        "total_completed": len(completed_jobs),
    }

    return flask.render_template("editor/projects.html", data=projects_data)


@editor.route("/projects/<int:job_id>")
@login_required
@editor_required
def project_detail(job_id):
    """View detailed project information."""
    editor_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    # Ensure this is the selected editor for this job
    if job.selectedEditorId != editor_data.editorId:
        flask.flash(
            "Access denied. You are not assigned to this project.", "danger"
        )
        return flask.redirect(flask.url_for("editor.projects"))

    # Get project messages
    project_messages = Message.getJobMessages(job_id)

    project_info = {
        "job": job,
        "creator": job.creator,
        "messages": project_messages,
        "can_upload_deliverable": job.status == "in_progress",
        "is_completed": job.status == "completed",
        "has_deliverable": bool(job.deliverableUrl),
    }

    return flask.render_template(
        "editor/project_detail.html", data=project_info
    )


@editor.route(
    "/projects/<int:job_id>/upload-deliverable", methods=["GET", "POST"]
)
@login_required
@editor_required
def upload_deliverable(job_id):
    """Upload final deliverable for project (FR-042)."""
    editor_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.selectedEditorId != editor_data.editorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("editor.projects"))

    if job.status != "in_progress":
        flask.flash("Cannot upload deliverable for this project.", "warning")
        return flask.redirect(
            flask.url_for("editor.project_detail", job_id=job_id)
        )

    form = DeliverableUploadForm()

    if form.validate_on_submit():
        try:
            success = editor_data.uploadDeliverable(
                job_id, form.deliverableUrl.data
            )

            if success:
                flask.flash("Deliverable uploaded successfully!", "success")
                return flask.redirect(
                    flask.url_for("editor.project_detail", job_id=job_id)
                )
            else:
                flask.flash("Failed to upload deliverable.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while uploading deliverable.", "danger"
            )

    return flask.render_template(
        "editor/upload_deliverable.html", job=job, form=form
    )


# ------------------------------------------------------------------------------
#                              COMMUNICATION (FR-043 to FR-046)
# ------------------------------------------------------------------------------
@editor.route("/messages")
@login_required
@editor_required
def messages():
    """View all messages and conversations."""
    conversations = Message.getActiveConversations(
        current_user.userId, limit=20
    )
    recent_messages = Message.getMessagesForUser(current_user.userId, "all")

    return flask.render_template(
        "editor/messages.html",
        conversations=conversations,
        recent_messages=recent_messages[:20],
    )


@editor.route("/messages/send", methods=["GET", "POST"])
@login_required
@editor_required
def send_message():
    """Send a message to a creator."""
    form = MessageForm()

    receiver_id = flask.request.args.get("receiver_id")
    job_id = flask.request.args.get("job_id")

    if receiver_id:
        form.receiverId.data = receiver_id
    if job_id:
        form.jobId.data = job_id

    if form.validate_on_submit():
        try:
            Message.sendMessage(
                senderId=current_user.userId,
                receiverId=int(form.receiverId.data),
                messageContent=form.messageContent.data,
                subject=form.subject.data,
                jobId=int(form.jobId.data) if form.jobId.data else None,
            )
            flask.flash("Message sent successfully!", "success")
            return flask.redirect(flask.url_for("editor.messages"))

        except Exception:
            db.session.rollback()
            flask.flash("Failed to send message. Please try again.", "danger")

    return flask.render_template("editor/send_message.html", form=form)


# ------------------------------------------------------------------------------
#                                 RATINGS (FR-051 to FR-054)
# ------------------------------------------------------------------------------
@editor.route("/ratings")
@login_required
@editor_required
def ratings():
    """View ratings given and received."""
    given_ratings = Rating.getRatingsByUser(current_user.userId)
    received_ratings = Rating.getRatingsForUser(current_user.userId)

    return flask.render_template(
        "editor/ratings.html",
        given_ratings=given_ratings,
        received_ratings=received_ratings,
    )


@editor.route("/ratings/submit", methods=["GET", "POST"])
@login_required
@editor_required
def submit_rating():
    """Submit a rating for a creator after job completion."""
    form = RatingForm()

    job_id = flask.request.args.get("job_id")
    creator_id = flask.request.args.get("creator_id")

    if job_id:
        form.jobId.data = job_id
    if creator_id:
        form.rateeId.data = creator_id

    if form.validate_on_submit():
        try:
            rating = Rating.createRating(
                jobId=int(form.jobId.data),
                raterId=current_user.userId,
                rateeId=int(form.rateeId.data),
                ratingValue=form.ratingValue.data,
                reviewText=form.reviewText.data,
            )

            if rating:
                flask.flash("Rating submitted successfully!", "success")
                return flask.redirect(flask.url_for("editor.ratings"))
            else:
                flask.flash(
                    "Failed to submit rating. You may have already rated this job.",
                    "warning",
                )

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while submitting the rating.", "danger"
            )

    return flask.render_template("editor/submit_rating.html", form=form)


# ------------------------------------------------------------------------------
#                              AJAX ENDPOINTS
# ------------------------------------------------------------------------------
@editor.route("/ajax/application-stats")
@login_required
@editor_required
def ajax_application_stats():
    """Get application statistics via AJAX."""
    editor_data = current_user.getSpecificUserData()

    stats = {
        "total_applications": len(editor_data.jobApplications),
        "pending_applications": len(editor_data.getActiveApplications()),
        "accepted_applications": len(editor_data.getAcceptedApplications()),
        "current_projects": len(editor_data.getCurrentJobs()),
        "completed_projects": len(editor_data.getCompletedJobs()),
        "verification_status": editor_data.isVerified,
        "portfolio_count": len(editor_data.portfolios),
        "verified_portfolio_count": len(editor_data.getVerifiedPortfolios()),
    }

    return flask.jsonify(stats)


@editor.route("/ajax/check-application", methods=["POST"])
@login_required
@editor_required
def ajax_check_application():
    """Check if editor has already applied for a job via AJAX."""
    try:
        data = flask.request.get_json()
        job_id = data.get("jobId")

        editor_data = current_user.getSpecificUserData()
        existing_application = JobApplication.checkExistingApplication(
            job_id, editor_data.editorId
        )

        return flask.jsonify(
            {
                "has_applied": bool(existing_application),
                "application_id": existing_application.jobApplicationId
                if existing_application
                else None,
                "application_status": existing_application.status
                if existing_application
                else None,
            }
        )

    except Exception:
        return (
            flask.jsonify({"error": "Failed to check application status"}),
            500,
        )


# ------------------------------------------------------------------------------
#                              UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
def send_application_notification(application):
    """Send email notification about job application to creator."""
    try:
        from ..utilities.email_sender import send_email

        job = application.job
        creator = job.creator.user
        editor = application.editor.user

        send_email(
            [creator.emailAddress],
            f"New Application for '{job.title}'",
            "email/new_application",
            creator=creator,
            editor=editor,
            job=job,
            application=application,
        )

        return True

    except Exception as e:
        flask.current_app.logger.error(
            f"Failed to send application notification: {str(e)}"
        )
        return False


def send_deliverable_notification(job, editor):
    """Send email notification about deliverable upload."""
    try:
        from ..utilities.email_sender import send_email

        creator = job.creator.user

        send_email(
            [creator.emailAddress],
            f"Deliverable Uploaded for '{job.title}'",
            "email/deliverable_uploaded",
            creator=creator,
            editor=editor,
            job=job,
        )

        return True

    except Exception as e:
        flask.current_app.logger.error(
            f"Failed to send deliverable notification: {str(e)}"
        )
        return False
