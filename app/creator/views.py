import flask
import json

from flask_login import current_user
from flask_login import login_required
from app.nlp.job_parser import parse_job_description

from decimal import Decimal

from . import creator
from .forms import RatingForm
from .forms import ReportForm
from .forms import MessageForm
from .forms import JobUpdateForm
from .forms import JobPostingForm
from .forms import EditorSearchForm
from .forms import ProfileUpdateForm
from .forms import JobCompletionForm
from .forms import PaymentInitiationForm

from app import db
from ..models import Job
from ..models import Rating
from ..models import Message
from ..models import Payment
from ..models import Editor
from ..models import Report
from ..models import Portfolio
from ..models import PaymentInterim
from ..models.user import User

import utilities.pesapal_payment as pesapal


def creator_required(f):
    """Decorator to ensure user is a creator."""

    def decorated_function(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or current_user.userType != "creator"
        ):
            flask.flash("Access denied. Creator account required.", "danger")
            return flask.redirect(flask.url_for("authentication.login"))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@creator.route("/dashboard")
@login_required
@creator_required
def dashboard():
    """Display creator dashboard with overview of jobs, payments, and activity."""
    creator_data = current_user.getSpecificUserData()

    # Get dashboard statistics
    total_jobs = len(creator_data.jobs)
    active_jobs = len(
        [
            job
            for job in creator_data.jobs
            if job.status in ["posted", "in_progress"]
        ]
    )
    completed_jobs = len(
        [job for job in creator_data.jobs if job.status == "completed"]
    )

    # Get recent jobs
    recent_jobs = (
        Job.query.filter_by(creatorId=creator_data.creatorId)
        .order_by(Job.dateCreated.desc())
        .limit(5)
        .all()
    )

    # Get pending applications count
    pending_applications = sum(
        len(job.getPendingApplications()) for job in creator_data.jobs
    )

    # Get recent messages
    recent_messages = Message.getMessagesForUser(
        current_user.userId, "received"
    )[:5]

    # Get payment statistics
    pending_payments = sum(
        1
        for job in creator_data.jobs
        if job.payment and job.payment.isPending()
    )
    completed_payments = sum(
        1
        for job in creator_data.jobs
        if job.payment and job.payment.isCompleted()
    )

    dashboard_data = {
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,
        "pending_applications": pending_applications,
        "pending_payments": pending_payments,
        "completed_payments": completed_payments,
        "recent_jobs": recent_jobs,
        "recent_messages": recent_messages,
    }

    return flask.render_template("creator/dashboard.html", data=dashboard_data)


@creator.route("/profile", methods=["GET", "POST"])
@login_required
@creator_required
def profile():
    """Display and update creator profile."""
    creator_data = current_user.getSpecificUserData()
    form = ProfileUpdateForm()

    if flask.request.method == "GET":
        form.fullName.data = current_user.fullName
        form.contentType.data = creator_data.contentType
        form.platformFocus.data = creator_data.platformFocus

    if form.validate_on_submit():
        try:
            current_user.fullName = form.fullName.data

            creator_data.updateContentPreferences(
                contentType=form.contentType.data,
                platformFocus=form.platformFocus.data,
            )

            db.session.commit()
            flask.flash("Profile updated successfully!", "success")
            return flask.redirect(flask.url_for("creator.profile"))

        except Exception:
            db.session.rollback()
            flask.flash("Failed to update profile. Please try again.", "danger")

    return flask.render_template("creator/profile.html", form=form)


# ------------------------------------------------------------------------------
#                                JOB MANAGEMENT
# ------------------------------------------------------------------------------
@creator.route("/jobs")
@login_required
@creator_required
def jobs():
    """Display all jobs posted by the creator."""
    creator_data = current_user.getSpecificUserData()
    status_filter = flask.request.args.get("status", "all")

    if status_filter == "posted":
        jobs_list = [job for job in creator_data.jobs if job.status == "posted"]
    elif status_filter == "in_progress":
        jobs_list = [
            job for job in creator_data.jobs if job.status == "in_progress"
        ]
    elif status_filter == "completed":
        jobs_list = [
            job for job in creator_data.jobs if job.status == "completed"
        ]
    else:
        jobs_list = creator_data.jobs

    jobs_list.sort(key=lambda x: x.dateCreated, reverse=True)

    return flask.render_template(
        "creator/jobs.html", jobs=jobs_list, status_filter=status_filter
    )


@creator.route("/jobs/new", methods=["GET", "POST"])
@login_required
@creator_required
def new_job():
    """Create a new job posting."""
    form = JobPostingForm()

   
    if form.validate_on_submit():
        try:
            # Step 1: Get the creator's job description
            description = form.description.data

            # Step 2: Process the description using spaCy
            nlp_results = parse_job_description(description)

            # Step 3: Display extracted NLP information
            print("\n========== NLP JOB ANALYSIS ==========")
            print("Job Description:", description)
            print("Extracted Skills:", nlp_results["skills"])
            print("Editing Styles:", nlp_results["styles"])
            print("Content Niches:", nlp_results["niches"])
            print("======================================\n")

            # Continue with the existing job creation process
            creator_data = current_user.getSpecificUserData()


            job_details = {
                "title": form.title.data,
                "description": form.description.data,
                "budgetMin": float(form.budgetMin.data)
                if form.budgetMin.data
                else None,
                "budgetMax": float(form.budgetMax.data)
                if form.budgetMax.data
                else None,
                "deadline": form.deadline.data,
                "requiredSkills": form.requiredSkills.data,

                # NLP extracted information
                "extractedSkills": nlp_results["skills"],
                "extractedStyles": nlp_results["styles"],
                "extractedNiches": nlp_results["niches"],

            }

            job = creator_data.postJob(job_details)
            flask.flash("Job posted successfully!", "success")
            return flask.redirect(
                flask.url_for("creator.job_detail", job_id=job.jobId)
            )

        except Exception:
            db.session.rollback()
            flask.flash("Failed to post job. Please try again.", "danger")

    return flask.render_template("creator/new_job.html", form=form)


@creator.route("/jobs/<int:job_id>")
@login_required
@creator_required
def job_detail(job_id):
    """Display detailed view of a specific job."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash("Access denied. You can only view your own jobs.", "danger")
        return flask.redirect(flask.url_for("creator.jobs"))

    applications = job.applications
    job_messages = Message.getJobMessages(job_id)
    payment = job.payment

    # Convert stored NLP JSON into Python lists
    nlp_skills = json.loads(job.extractedSkills or "[]")
    nlp_styles = json.loads(job.extractedStyles or "[]")
    nlp_niches = json.loads(job.extractedNiches or "[]")


    return flask.render_template(
        "creator/job_detail.html",
        job=job,
        applications=applications,
        messages=job_messages,
        payment=payment,
        nlp_skills=nlp_skills,
        nlp_styles=nlp_styles,
        nlp_niches=nlp_niches,
    )


@creator.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
@creator_required
def edit_job(job_id):
    """Edit an existing job posting (only if status is 'posted')."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash("Access denied. You can only edit your own jobs.", "danger")
        return flask.redirect(flask.url_for("creator.jobs"))

    if job.status != "posted":
        flask.flash(
            "Cannot edit jobs that are in progress or completed.", "warning"
        )
        return flask.redirect(
            flask.url_for("creator.job_detail", job_id=job_id)
        )

    form = JobUpdateForm()

    if flask.request.method == "GET":
        form.title.data = job.title
        form.description.data = job.description
        form.budgetMin.data = job.budgetMin
        form.budgetMax.data = job.budgetMax
        form.deadline.data = job.deadline
        form.requiredSkills.data = job.requiredSkills

    if form.validate_on_submit():
        try:
            success = job.updateJobDetails(
                title=form.title.data,
                description=form.description.data,
                budgetMin=float(form.budgetMin.data)
                if form.budgetMin.data
                else None,
                budgetMax=float(form.budgetMax.data)
                if form.budgetMax.data
                else None,
                deadline=form.deadline.data,
                requiredSkills=form.requiredSkills.data,
            )

            if success:
                flask.flash("Job updated successfully!", "success")
                return flask.redirect(
                    flask.url_for("creator.job_detail", job_id=job_id)
                )
            else:
                flask.flash("Cannot update job in current status.", "warning")

        except Exception:
            db.session.rollback()
            flask.flash("Failed to update job. Please try again.", "danger")

    return flask.render_template("creator/edit_job.html", form=form, job=job)


@creator.route("/jobs/<int:job_id>/applications")
@login_required
@creator_required
def job_applications(job_id):
    """View all applications for a specific job."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash(
            "Access denied. You can only view applications for your own jobs.",
            "danger",
        )
        return flask.redirect(flask.url_for("creator.jobs"))

    applications = job.applications
    pending_applications = job.getPendingApplications()
    accepted_application = job.getAcceptedApplication()

    return flask.render_template(
        "creator/job_applications.html",
        job=job,
        applications=applications,
        pending_applications=pending_applications,
        accepted_application=accepted_application,
    )


@creator.route("/jobs/<int:job_id>/select-editor", methods=["POST"])
@login_required
@creator_required
def select_editor(job_id):
    """Select an editor for a job."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.jobs"))

    editor_id = flask.request.form.get("editorId")
    if not editor_id:
        flask.flash("No editor selected.", "warning")
        return flask.redirect(
            flask.url_for("creator.job_applications", job_id=job_id)
        )

    try:
        success = creator_data.selectEditorForJob(job_id, int(editor_id))
        if success:
            flask.flash(
                "Editor selected successfully! Job is now in progress.",
                "success",
            )
        else:
            flask.flash(
                "Failed to select editor. Job may not be in correct status.",
                "danger",
            )

    except Exception:
        db.session.rollback()
        flask.flash("An error occurred while selecting the editor.", "danger")

    return flask.redirect(flask.url_for("creator.job_detail", job_id=job_id))


@creator.route("/jobs/<int:job_id>/complete", methods=["GET", "POST"])
@login_required
@creator_required
def complete_job(job_id):
    """Mark a job as completed."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.jobs"))

    form = JobCompletionForm()

    if form.validate_on_submit():
        try:
            success = creator_data.markJobCompleted(
                job_id, deliverableUrl=form.deliverableUrl.data
            )
            if success:
                flask.flash("Job marked as completed successfully!", "success")
                return flask.redirect(
                    flask.url_for("creator.job_detail", job_id=job_id)
                )
            else:
                flask.flash("Cannot complete job in current status.", "warning")

        except Exception:
            db.session.rollback()
            flask.flash("Failed to complete job. Please try again.", "danger")

    return flask.render_template(
        "creator/complete_job.html", form=form, job=job
    )


# ------------------------------------------------------------------------------
#                              EDITOR DISCOVERY
# ------------------------------------------------------------------------------
@creator.route("/editors")
@login_required
@creator_required
def editors():
    """Browse and search verified editors."""
    form = EditorSearchForm()
    editors_list = []

    if flask.request.method == "GET" and flask.request.args:
        search_term = flask.request.args.get("searchTerm", "").strip()
        experience_level = flask.request.args.get("experienceLevel", "")
        max_budget = flask.request.args.get("maxBudget", "")
        skill_filter = flask.request.args.get("skillFilter", "").strip()
        verified_only = flask.request.args.get("verifiedOnly", "")

        query = Editor.query

        if verified_only == "verified":
            query = query.filter(Editor.isVerified == True)
        elif verified_only == "unverified":
            query = query.filter(Editor.isVerified == False)
        else:
            query = query.filter(Editor.isVerified == True)

        if experience_level:
            query = query.filter(Editor.experienceLevel == experience_level)

        if max_budget:
            try:
                budget_limit = float(max_budget)
                query = query.filter(Editor.hourlyRate <= budget_limit)
            except ValueError:
                pass

        if skill_filter:
            query = query.filter(
                Editor.specializations.like(f"%{skill_filter}%")
            )

        if search_term:
            query = query.join(Editor).filter(
                (Editor.fullName.like(f"%{search_term}%"))
                | (Editor.specializations.like(f"%{search_term}%"))
            )

        editors_list = query.all()

        # Pre-populate form
        form.searchTerm.data = search_term
        form.experienceLevel.data = experience_level
        form.maxBudget.data = Decimal(max_budget) if max_budget else None
        form.skillFilter.data = skill_filter
        form.verifiedOnly.data = verified_only
    else:
        editors_list = Editor.getVerifiedEditors()

    return flask.render_template(
        "creator/editors.html", editors=editors_list, form=form
    )


@creator.route("/editors/<int:editor_id>")
@login_required
@creator_required
def editor_profile(editor_id):
    """View detailed editor profile and portfolio."""
    editor = Editor.query.get_or_404(editor_id)
    portfolios = editor.getVerifiedPortfolios()
    completed_jobs = editor.getCompletedJobs()

    return flask.render_template(
        "creator/editor_profile.html",
        editor=editor,
        portfolios=portfolios,
        completed_jobs_count=len(completed_jobs),
    )


# ------------------------------------------------------------------------------
#                              COMMUNICATION
# ------------------------------------------------------------------------------
@creator.route("/messages")
@login_required
@creator_required
def messages():
    """View all messages and conversations."""
    conversations = Message.getActiveConversations(
        current_user.userId, limit=20
    )
    recent_messages = Message.getMessagesForUser(current_user.userId, "all")

    return flask.render_template(
        "creator/messages.html",
        conversations=conversations,
        recent_messages=recent_messages[:20],
    )


@creator.route("/messages/send", methods=["GET", "POST"])
@login_required
@creator_required
def send_message():
    """Send a message to an editor."""
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
            return flask.redirect(flask.url_for("creator.messages"))

        except Exception:
            db.session.rollback()
            flask.flash("Failed to send message. Please try again.", "danger")

    return flask.render_template("creator/send_message.html", form=form)


# ------------------------------------------------------------------------------
#                                 RATINGS
# ------------------------------------------------------------------------------
@creator.route("/ratings")
@login_required
@creator_required
def ratings():
    """View ratings given and received."""
    given_ratings = Rating.getRatingsByUser(current_user.userId)
    received_ratings = Rating.getRatingsForUser(current_user.userId)

    return flask.render_template(
        "creator/ratings.html",
        given_ratings=given_ratings,
        received_ratings=received_ratings,
    )


@creator.route("/ratings/submit", methods=["GET", "POST"])
@login_required
@creator_required
def submit_rating():
    """Submit a rating for an editor after job completion."""
    form = RatingForm()

    job_id = flask.request.args.get("job_id")
    editor_id = flask.request.args.get("editor_id")

    if job_id:
        form.jobId.data = job_id
    if editor_id:
        form.rateeId.data = editor_id

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
                return flask.redirect(flask.url_for("creator.ratings"))
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

    return flask.render_template("creator/submit_rating.html", form=form)


# ------------------------------------------------------------------------------
#                              PAYMENT MANAGEMENT - PESAPAL INTEGRATED
# ------------------------------------------------------------------------------
@creator.route("/payments")
@login_required
@creator_required
def payments():
    """View payment history and pending payments."""
    creator_data = current_user.getSpecificUserData()

    all_payments = []
    for job in creator_data.jobs:
        if job.payment:
            all_payments.append(job.payment)

    all_payments.sort(key=lambda x: x.dateCreated, reverse=True)

    pending_payments = [p for p in all_payments if p.isPending()]
    completed_payments = [p for p in all_payments if p.isCompleted()]

    return flask.render_template(
        "creator/payments.html",
        all_payments=all_payments,
        pending_payments=pending_payments,
        completed_payments=completed_payments,
    )


@creator.route("/payments/initiate/<int:job_id>", methods=["GET", "POST"])
@login_required
@creator_required
def initiate_payment(job_id):
    """Initiate payment process for a completed job."""
    creator_data = current_user.getSpecificUserData()
    job = Job.query.get_or_404(job_id)

    if job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    if job.status != "completed":
        flask.flash(
            "Payment can only be initiated for completed jobs.", "warning"
        )
        return flask.redirect(
            flask.url_for("creator.job_detail", job_id=job_id)
        )

    if job.payment:
        flask.flash("Payment already exists for this job.", "warning")
        return flask.redirect(flask.url_for("creator.payments"))

    form = PaymentInitiationForm()
    form.jobId.data = job_id

    if form.validate_on_submit():
        try:
            # Create payment agreement
            payment = Payment.createPaymentAgreement(
                jobId=job_id, agreedAmount=float(form.agreedAmount.data)
            )

            flask.flash("Payment agreement created successfully!", "success")
            return flask.redirect(
                flask.url_for(
                    "creator.process_payment", payment_id=payment.paymentId
                )
            )

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to initiate payment. Please try again.", "danger"
            )

    return flask.render_template(
        "creator/initiate_payment.html", form=form, job=job
    )


@creator.route("/payments/process/<int:payment_id>", methods=["GET", "POST"])
@login_required
@creator_required
def process_payment(payment_id):
    """Process payment through Pesapal gateway."""
    payment = Payment.query.get_or_404(payment_id)

    creator_data = current_user.getSpecificUserData()
    if payment.job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    if flask.request.method == "POST":
        try:
            # Get Pesapal access token
            access_token = pesapal.get_access_token().get("token")
            if not access_token:
                flask.flash(
                    "Payment processing temporarily unavailable. Please try again later.",
                    "warning",
                )
                return flask.redirect(flask.url_for("creator.payments"))

            # Get IPN URL and ID
            ipn_url = flask.url_for(
                "creator.pesapal_payment_callback", _external=True
            )
            ipn_response = pesapal.get_notification_id(access_token, ipn_url)
            ipn_id = ipn_response.get("ipn_id")

            if not ipn_id:
                flask.flash(
                    "Payment processing temporarily unavailable. Please try again later.",
                    "warning",
                )
                return flask.redirect(flask.url_for("creator.payments"))

            # Prepare customer name
            first_name, middle_name, last_name = pesapal.split_full_name(
                current_user.fullName
            )

            # Create payment request
            payment_request = {
                "amount": float(payment.agreedAmount),
                "description": f"Payment for job: {payment.job.title}",
                "callback_url": flask.url_for(
                    "creator.pesapal_payment_callback", _external=True
                ),
                "notification_id": ipn_id,
                "email_address": current_user.emailAddress,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
            }

            # Get iframe URL
            iframe_response = pesapal.get_merchant_order_url(
                payment_request, access_token
            )

            if not iframe_response.get("order_tracking_id"):
                flask.flash(
                    "Payment processing temporarily unavailable. Please try again later.",
                    "warning",
                )
                return flask.redirect(flask.url_for("creator.payments"))

            # Create interim payment record
            interim_payment_data = {
                "paymentId": payment.paymentId,
                "orderTrackingId": iframe_response.get("order_tracking_id"),
                "merchantReference": iframe_response.get("merchant_reference"),
                "iframeSrc": iframe_response.get("redirect_url"),
                "status": "SAVED",
            }

            interim = PaymentInterim(**interim_payment_data)
            db.session.add(interim)
            db.session.commit()

            return flask.render_template(
                "creator/payment_iframe.html",
                iframe_src=iframe_response.get("redirect_url"),
                payment=payment,
            )

        except Exception:
            db.session.rollback()
            flask.flash(
                "Failed to process payment. Please try again.", "danger"
            )
            return flask.redirect(flask.url_for("creator.payments"))

    return flask.render_template(
        "creator/process_payment.html", payment=payment
    )


@creator.route("/payments/pesapal/callback")
def pesapal_payment_callback():
    """Handle Pesapal payment callback and update payment status."""
    order_tracking_id = flask.request.args.get("OrderTrackingId")

    if not order_tracking_id:
        flask.flash("Invalid payment response received.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    try:
        # Get access token and check transaction status
        access_token = pesapal.get_access_token().get("token")
        if not access_token:
            flask.flash(
                "Unable to verify payment status. Please contact support.",
                "danger",
            )
            return flask.redirect(flask.url_for("creator.payments"))

        status = pesapal.get_transaction_status(order_tracking_id, access_token)
        payment_status = status.get("payment_status_description")

        # Retrieve interim payment record
        interim_payment = PaymentInterim.query.filter_by(
            orderTrackingId=order_tracking_id
        ).first()
        if not interim_payment:
            flask.flash(
                "Payment record not found. Please contact support.", "danger"
            )
            return flask.redirect(flask.url_for("creator.payments"))

        payment = Payment.query.get_or_404(interim_payment.paymentId)

        # Handle different payment statuses
        if payment_status == "Completed":
            # Update payment
            payment.updatePaymentStatus(
                newStatus="paid",
                paymentMethod=f"Pesapal - {status.get('payment_method')}",
                reference=status.get("confirmation_code"),
            )

            # Update interim payment
            interim_payment.markAsCompleted()

            flask.flash(
                f"Payment successful! Receipt number: {status.get('confirmation_code')}. "
                f"Amount: {status.get('currency')} {status.get('amount')} via {status.get('payment_method')}",
                "success",
            )

            # Mark payment as completed for final step
            payment.markAsCompleted()

            return flask.redirect(
                flask.url_for(
                    "creator.payment_success", payment_id=payment.paymentId
                )
            )

        elif payment_status == "Pending":
            flask.flash(
                "Your payment is being processed. We will notify you once confirmed.",
                "warning",
            )
            return flask.redirect(flask.url_for("creator.payments"))

        else:  # Failed or Invalid
            payment.updatePaymentStatus(
                newStatus="agreed"
            )  # Reset to agreed status
            interim_payment.markAsFailed()

            flask.flash(
                f"Payment failed: {status.get('message')}. Please try again or contact support.",
                "danger",
            )
            return flask.redirect(
                flask.url_for(
                    "creator.payment_success", payment_id=payment.paymentId
                )
            )

    except Exception:
        flask.flash(
            "Error processing payment callback. Please contact support.",
            "danger",
        )
        return flask.redirect(flask.url_for("creator.payments"))


@creator.route("/payments/success/<int:payment_id>")
@login_required
@creator_required
def payment_success(payment_id):
    """Display payment success page."""
    payment = Payment.query.get_or_404(payment_id)

    creator_data = current_user.getSpecificUserData()
    if payment.job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    return flask.render_template(
        "creator/payment_success.html", payment=payment
    )


@creator.route("/payments/invoice/<int:payment_id>")
@login_required
@creator_required
def payment_invoice(payment_id):
    """Generate and display payment invoice."""
    payment = Payment.query.get_or_404(payment_id)

    creator_data = current_user.getSpecificUserData()
    if payment.job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    if not payment.invoiceNumber:
        payment.generateInvoiceNumber()

    return flask.render_template(
        "creator/payment_invoice.html", payment=payment
    )


@creator.route("/payments/status/<int:payment_id>")
@login_required
@creator_required
def payment_status(payment_id):
    """Check and display payment status."""
    payment = Payment.query.get_or_404(payment_id)

    creator_data = current_user.getSpecificUserData()
    if payment.job.creatorId != creator_data.creatorId:
        flask.flash("Access denied.", "danger")
        return flask.redirect(flask.url_for("creator.payments"))

    return flask.render_template("creator/payment_status.html", payment=payment)


# ------------------------------------------------------------------------------
#                              CONTENT REPORTING
# ------------------------------------------------------------------------------
@creator.route("/report", methods=["GET", "POST"])
@login_required
@creator_required
def submit_report():
    """Submit a report for inappropriate content or behavior."""
    form = ReportForm()

    reported_user_id = flask.request.args.get("user_id")
    reported_portfolio_id = flask.request.args.get("portfolio_id")

    if reported_user_id:
        form.reportedUserId.data = reported_user_id
    if reported_portfolio_id:
        form.reportedPortfolioId.data = reported_portfolio_id

    if form.validate_on_submit():
        try:
            report = Report.submitReport(
                reporterId=current_user.userId,
                reportReason=form.reportReason.data,
                reportedUserId=int(form.reportedUserId.data)
                if form.reportedUserId.data
                else None,
                reportedPortfolioId=int(form.reportedPortfolioId.data)
                if form.reportedPortfolioId.data
                else None,
            )

            if report:
                flask.flash(
                    "Report submitted successfully. It will be reviewed by our team.",
                    "success",
                )
                return flask.redirect(flask.url_for("creator.dashboard"))
            else:
                flask.flash(
                    "Failed to submit report. You may have already reported this content.",
                    "warning",
                )

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while submitting the report.", "danger"
            )

    return flask.render_template("creator/submit_report.html", form=form)


# ------------------------------------------------------------------------------
#                              SEARCH AND FILTERS
# ------------------------------------------------------------------------------
@creator.route("/search")
@login_required
@creator_required
def search():
    """Global search functionality for editors and portfolios."""
    query = flask.request.args.get("q", "").strip()
    search_type = flask.request.args.get(
        "type", "editors"
    )  # 'editors' or 'portfolios'

    results = []

    if query:
        if search_type == "editors":
            # Search editors
            results = (
                Editor.query.join(User)
                .filter(
                    Editor.isVerified == True,
                    (User.fullName.like(f"%{query}%"))
                    | (Editor.specializations.like(f"%{query}%")),
                )
                .all()
            )
        elif search_type == "portfolios":
            # Search portfolios
            results = Portfolio.query.filter(
                Portfolio.verificationStatus == "approved",
                (Portfolio.title.like(f"%{query}%"))
                | (Portfolio.description.like(f"%{query}%"))
                | (Portfolio.skillTags.like(f"%{query}%")),
            ).all()

    return flask.render_template(
        "creator/search_results.html",
        results=results,
        query=query,
        search_type=search_type,
    )


# ------------------------------------------------------------------------------
#                              ADVANCED FEATURES
# ------------------------------------------------------------------------------


@creator.route("/ajax/editor-contact", methods=["POST"])
@login_required
@creator_required
def ajax_editor_contact():
    """Quick contact form for editors via AJAX."""
    try:
        data = flask.request.get_json()

        Message.sendMessage(
            senderId=current_user.userId,
            receiverId=data.get("editorId"),
            messageContent=data.get("message"),
            subject=data.get("subject", "Project Inquiry"),
        )

        return flask.jsonify(
            {"success": True, "message": "Message sent successfully!"}
        )

    except Exception:
        return (
            flask.jsonify(
                {"success": False, "error": "Failed to send message"}
            ),
            500,
        )


def get_sidebar_data(creator_data):
    """
    Helper function to generate consistent sidebar data for all creator views.

    :param creator_data: Creator object
    :return: dict - Dictionary containing sidebar data
    """
    # Calculate active jobs
    active_jobs = len(
        [
            job
            for job in creator_data.jobs
            if job.status in ["posted", "in_progress"]
        ]
    )

    # Get recent messages
    recent_messages = Message.getMessagesForUser(
        current_user.userId, "received"
    )[:5]

    # Calculate pending payments
    pending_payments = sum(
        1
        for job in creator_data.jobs
        if job.payment and job.payment.isPending()
    )

    return {
        "active_jobs": active_jobs,
        "recent_messages": recent_messages,
        "pending_payments": pending_payments,
    }


@creator.route("/analytics")
@login_required
@creator_required
def analytics():
    """Display creator analytics and insights."""
    creator_data = current_user.getSpecificUserData()

    # Get sidebar data
    sidebar_data = get_sidebar_data(creator_data)

    # Calculate analytics
    total_jobs = len(creator_data.jobs)
    total_spent = sum(
        float(job.payment.agreedAmount)
        for job in creator_data.jobs
        if job.payment and job.payment.isCompleted()
    )

    # Job status distribution
    job_statuses = {
        "posted": len([j for j in creator_data.jobs if j.status == "posted"]),
        "in_progress": len(
            [j for j in creator_data.jobs if j.status == "in_progress"]
        ),
        "completed": len(
            [j for j in creator_data.jobs if j.status == "completed"]
        ),
    }

    # Average job completion time
    completed_jobs = [j for j in creator_data.jobs if j.status == "completed"]
    avg_completion_days = 0
    if completed_jobs:
        total_days = sum(
            (job.lastUpdated - job.dateCreated).days for job in completed_jobs
        )
        avg_completion_days = total_days / len(completed_jobs)

    # Top editors worked with
    editor_counts = {}
    for job in creator_data.jobs:
        if job.selectedEditor:
            editor_id = job.selectedEditor.editorId
            editor_counts[editor_id] = editor_counts.get(editor_id, 0) + 1

    top_editors = []
    for editor_id, count in sorted(
        editor_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        editor = Editor.query.get(editor_id)
        if editor:
            top_editors.append({"editor": editor, "job_count": count})

    # Combine analytics data with sidebar data
    analytics_data = {
        **sidebar_data,  # Spread sidebar data
        "total_jobs": total_jobs,
        "total_spent": total_spent,
        "job_statuses": job_statuses,
        "avg_completion_days": round(avg_completion_days, 1),
        "top_editors": top_editors,
        "success_rate": (job_statuses["completed"] / total_jobs * 100)
        if total_jobs > 0
        else 0,
    }

    return flask.render_template("creator/analytics.html", data=analytics_data)
