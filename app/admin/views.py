import flask

from flask_login import current_user
from flask_login import login_required

from datetime import datetime

from . import admin
from .forms import AdminSearchForm
from .forms import UserSuspensionForm
from .forms import UserPasswordResetForm
from .forms import ReportResolutionForm
from .forms import PortfolioVerificationForm

from app import db
from ..models import Job
from ..models.user import User
from ..models import Rating
from ..models import Report
from ..models import Portfolio


def admin_required(f):
    """Decorator to ensure user is an admin."""

    def decorated_function(*args, **kwargs):
        if (
            not current_user.is_authenticated
            or current_user.userType != "admin"
        ):
            flask.flash(
                "Access denied. Administrator account required.", "danger"
            )
            return flask.redirect(flask.url_for("authentication.login"))
        return f(*args, **kwargs)

    decorated_function.__name__ = f.__name__
    return decorated_function


@admin.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Display admin dashboard with system statistics and recent activity."""
    admin_data = current_user.getSpecificUserData()

    # Get system statistics (FR-061, FR-062, FR-063, FR-064)
    stats = admin_data.getSystemStatistics()

    # Get pending items requiring admin attention
    pending_portfolios = admin_data.getPendingPortfolios()
    pending_reports = admin_data.getPendingReports()

    # Get recent platform activity
    recent_jobs = Job.getRecentJobs(limit=5)
    recent_ratings = Rating.getRecentRatings(limit=5)

    # Additional statistics
    stats.update(
        {
            "pending_portfolios": len(pending_portfolios),
            "pending_reports": len(pending_reports),
            "recent_activity_count": len(recent_jobs) + len(recent_ratings),
        }
    )

    dashboard_data = {
        "statistics": stats,
        "pending_portfolios": pending_portfolios[:10],  # Show top 10
        "pending_reports": pending_reports[:10],
        "recent_jobs": recent_jobs,
        "recent_ratings": recent_ratings,
    }

    return flask.render_template("admin/dashboard.html", data=dashboard_data)


# ------------------------------------------------------------------------------
#                              USER MANAGEMENT (FR-055 to FR-057)
# ------------------------------------------------------------------------------
@admin.route("/users")
@login_required
@admin_required
def users():
    """View all user accounts with filtering options."""
    user_type = flask.request.args.get("type", "all")
    status = flask.request.args.get("status", "all")
    search = flask.request.args.get("search", "").strip()

    # Build query
    query = User.query

    # Filter by user type
    if user_type != "all":
        query = query.filter(User.userType == user_type)

    # Filter by status
    if status == "active":
        query = query.filter(User.isActive == True)
    elif status == "suspended":
        query = query.filter(User.isActive == False)

    # Search by name or email
    if search:
        query = query.filter(
            (User.fullName.like(f"%{search}%"))
            | (User.emailAddress.like(f"%{search}%"))
        )

    users_list = query.order_by(User.dateCreated.desc()).all()

    return flask.render_template(
        "admin/users.html",
        users=users_list,
        user_type=user_type,
        status=status,
        search=search,
    )


@admin.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    """View detailed information about a specific user."""
    user = User.query.get_or_404(user_id)

    # Get user-specific data
    specific_data = user.getSpecificUserData()

    # Get user's activity
    sent_messages = user.sentMessages[:10]
    received_ratings = user.receivedRatings[:10]
    reports_about_user = Report.getReportsForUser(user_id)

    user_info = {
        "user": user,
        "specific_data": specific_data,
        "sent_messages": sent_messages,
        "received_ratings": received_ratings,
        "reports_count": len(reports_about_user),
        "recent_reports": reports_about_user[:5],
    }

    return flask.render_template("admin/user_detail.html", data=user_info)


@admin.route("/users/<int:user_id>/suspend", methods=["GET", "POST"])
@login_required
@admin_required
def suspend_user(user_id):
    """Suspend a user account."""
    user = User.query.get_or_404(user_id)
    form = UserSuspensionForm()

    if form.validate_on_submit():
        try:
            admin_data = current_user.getSpecificUserData()
            success = admin_data.suspendUser(user_id, reason=form.reason.data)

            if success:
                flask.flash(
                    f"User {user.fullName} has been suspended.", "success"
                )
                return flask.redirect(
                    flask.url_for("admin.user_detail", user_id=user_id)
                )
            else:
                flask.flash("Failed to suspend user.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while suspending the user.", "danger"
            )

    return flask.render_template(
        "admin/suspend_user.html", user=user, form=form
    )


@admin.route("/users/<int:user_id>/reactivate", methods=["POST"])
@login_required
@admin_required
def reactivate_user(user_id):
    """Reactivate a suspended user account."""
    try:
        admin_data = current_user.getSpecificUserData()
        success = admin_data.reactivateUser(user_id)

        if success:
            user = User.query.get(user_id)
            flask.flash(
                f"User {user.fullName} has been reactivated.", "success"
            )
        else:
            flask.flash("Failed to reactivate user.", "danger")

    except Exception:
        db.session.rollback()
        flask.flash("An error occurred while reactivating the user.", "danger")

    return flask.redirect(flask.url_for("admin.user_detail", user_id=user_id))


@admin.route("/users/<int:user_id>/reset-password", methods=["GET", "POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    """Reset a user's password (FR-057)."""
    user = User.query.get_or_404(user_id)
    form = UserPasswordResetForm()

    if form.validate_on_submit():
        try:
            admin_data = current_user.getSpecificUserData()
            reset_token = admin_data.resetUserPassword(user_id)

            if reset_token:
                # In a real system, you'd email this token to the user
                flask.flash(
                    f"Password reset initiated for {user.fullName}. "
                    f"Reset token: {reset_token[:8]}... (Full token would be emailed)",
                    "success",
                )
                return flask.redirect(
                    flask.url_for("admin.user_detail", user_id=user_id)
                )
            else:
                flask.flash("Failed to initiate password reset.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash("An error occurred while resetting password.", "danger")

    return flask.render_template(
        "admin/reset_password.html", user=user, form=form
    )


# ------------------------------------------------------------------------------
#                           PORTFOLIO VERIFICATION (FR-024 to FR-027)
# ------------------------------------------------------------------------------
@admin.route("/portfolios")
@login_required
@admin_required
def portfolios():
    """View portfolio submissions for verification."""
    status_filter = flask.request.args.get("status", "pending")

    if status_filter == "approved":
        portfolios_list = Portfolio.query.filter_by(
            verificationStatus="approved"
        ).all()
    elif status_filter == "rejected":
        portfolios_list = Portfolio.query.filter_by(
            verificationStatus="rejected"
        ).all()
    else:  # pending
        portfolios_list = Portfolio.getPendingPortfolios()

    portfolios_list.sort(key=lambda x: x.dateCreated, reverse=True)

    return flask.render_template(
        "admin/portfolios.html",
        portfolios=portfolios_list,
        status_filter=status_filter,
    )


@admin.route("/portfolios/<int:portfolio_id>")
@login_required
@admin_required
def portfolio_detail(portfolio_id):
    """View detailed portfolio information for verification."""
    portfolio = Portfolio.query.get_or_404(portfolio_id)

    # Get editor information
    editor = portfolio.editor
    editor_user = editor.user if editor else None

    # Get other portfolios by this editor
    other_portfolios = [
        p for p in editor.portfolios if p.portfolioId != portfolio_id
    ]

    portfolio_info = {
        "portfolio": portfolio,
        "editor": editor,
        "editor_user": editor_user,
        "other_portfolios": other_portfolios,
        "skill_tags": portfolio.getSkillTagsList(),
    }

    return flask.render_template(
        "admin/portfolio_detail.html", data=portfolio_info
    )


@admin.route("/portfolios/<int:portfolio_id>/verify", methods=["GET", "POST"])
@login_required
@admin_required
def verify_portfolio(portfolio_id):
    """Approve or reject a portfolio submission."""
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    form = PortfolioVerificationForm()

    if form.validate_on_submit():
        try:
            admin_data = current_user.getSpecificUserData()
            approved = form.decision.data == "approve"
            notes = form.notes.data if form.notes.data else None

            success = admin_data.verifyPortfolio(portfolio_id, approved, notes)

            if success:
                action = "approved" if approved else "rejected"
                flask.flash(f"Portfolio has been {action}.", "success")
                return flask.redirect(flask.url_for("admin.portfolios"))
            else:
                flask.flash("Failed to verify portfolio.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while verifying the portfolio.", "danger"
            )

    return flask.render_template(
        "admin/verify_portfolio.html", portfolio=portfolio, form=form
    )


# ------------------------------------------------------------------------------
#                           CONTENT MODERATION (FR-058 to FR-060)
# ------------------------------------------------------------------------------
@admin.route("/reports")
@login_required
@admin_required
def reports():
    """View and manage user reports."""
    status_filter = flask.request.args.get("status", "pending")

    if status_filter == "resolved":
        reports_list = Report.getResolvedReports()
    elif status_filter == "reviewed":
        reports_list = Report.query.filter_by(reportStatus="reviewed").all()
    else:  # pending
        reports_list = Report.getPendingReports()

    return flask.render_template(
        "admin/reports.html", reports=reports_list, status_filter=status_filter
    )


@admin.route("/reports/<int:report_id>")
@login_required
@admin_required
def report_detail(report_id):
    """View detailed report information."""
    report = Report.query.get_or_404(report_id)

    # Get context based on report type
    context = {
        "report": report,
        "report_details": report.getReportDetails(),
        "report_type": report.getReportType(),
    }

    return flask.render_template("admin/report_detail.html", data=context)


@admin.route("/reports/<int:report_id>/resolve", methods=["GET", "POST"])
@login_required
@admin_required
def resolve_report(report_id):
    """Resolve a user report with appropriate action."""
    report = Report.query.get_or_404(report_id)
    form = ReportResolutionForm()

    if form.validate_on_submit():
        try:
            admin_data = current_user.getSpecificUserData()
            success = admin_data.resolveReport(
                report_id,
                resolution=form.resolution.data,
                adminNotes=form.admin_notes.data,
            )

            if success:
                flask.flash("Report has been resolved.", "success")
                return flask.redirect(flask.url_for("admin.reports"))
            else:
                flask.flash("Failed to resolve report.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while resolving the report.", "danger"
            )

    return flask.render_template(
        "admin/resolve_report.html", report=report, form=form
    )


@admin.route("/portfolios/<int:portfolio_id>/remove", methods=["POST"])
@login_required
@admin_required
def remove_portfolio_content(portfolio_id):
    """Remove inappropriate portfolio content."""
    reason = flask.request.form.get("reason", "Inappropriate content")

    try:
        admin_data = current_user.getSpecificUserData()
        success = admin_data.removeInappropriateContent(portfolio_id, reason)

        if success:
            flask.flash("Portfolio content has been removed.", "success")
        else:
            flask.flash("Failed to remove content.", "danger")

    except Exception:
        db.session.rollback()
        flask.flash("An error occurred while removing content.", "danger")

    return flask.redirect(flask.url_for("admin.portfolios"))


# ------------------------------------------------------------------------------
#                              SEARCH AND FILTERS
# ------------------------------------------------------------------------------
@admin.route("/search")
@login_required
@admin_required
def search():
    """Global admin search functionality."""
    form = AdminSearchForm()
    results = []

    query = flask.request.args.get("q", "").strip()
    search_type = flask.request.args.get("type", "users")

    if query:
        if search_type == "users":
            results = User.query.filter(
                (User.fullName.like(f"%{query}%"))
                | (User.emailAddress.like(f"%{query}%"))
            ).all()

        elif search_type == "portfolios":
            results = Portfolio.query.filter(
                (Portfolio.title.like(f"%{query}%"))
                | (Portfolio.description.like(f"%{query}%"))
            ).all()

        elif search_type == "jobs":
            results = Job.query.filter(
                (Job.title.like(f"%{query}%"))
                | (Job.description.like(f"%{query}%"))
            ).all()

    return flask.render_template(
        "admin/search_results.html",
        results=results,
        query=query,
        search_type=search_type,
        form=form,
    )


# ------------------------------------------------------------------------------
#                              AJAX ENDPOINTS
# ------------------------------------------------------------------------------
@admin.route("/ajax/system-stats")
@login_required
@admin_required
def ajax_system_stats():
    """Get real-time system statistics via AJAX."""
    admin_data = current_user.getSpecificUserData()
    stats = admin_data.getSystemStatistics()

    # Add pending counts
    stats.update(
        {
            "pending_portfolios": len(admin_data.getPendingPortfolios()),
            "pending_reports": len(admin_data.getPendingReports()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    return flask.jsonify(stats)


@admin.route("/ajax/quick-action", methods=["POST"])
@login_required
@admin_required
def ajax_quick_action():
    """Handle quick admin actions via AJAX."""
    try:
        data = flask.request.get_json()
        action = data.get("action")
        target_id = data.get("target_id")

        admin_data = current_user.getSpecificUserData()

        if action == "approve_portfolio":
            success = admin_data.verifyPortfolio(target_id, True)
            message = "Portfolio approved" if success else "Failed to approve"

        elif action == "reject_portfolio":
            success = admin_data.verifyPortfolio(
                target_id, False, "Quick rejection"
            )
            message = "Portfolio rejected" if success else "Failed to reject"

        elif action == "suspend_user":
            success = admin_data.suspendUser(target_id, "Administrative action")
            message = "User suspended" if success else "Failed to suspend"

        else:
            return (
                flask.jsonify({"success": False, "message": "Unknown action"}),
                400,
            )

        return flask.jsonify({"success": success, "message": message})

    except Exception:
        return (
            flask.jsonify({"success": False, "message": "Action failed"}),
            500,
        )


# ------------------------------------------------------------------------------
#                              ERROR HANDLERS
# ------------------------------------------------------------------------------
@admin.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors within admin blueprint."""
    return flask.render_template("admin/errors/404.html"), 404


@admin.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors within admin blueprint."""
    return flask.render_template("admin/errors/403.html"), 403


@admin.errorhandler(500)
def internal_error(error):
    """Handle 500 errors within admin blueprint."""
    db.session.rollback()
    return flask.render_template("admin/errors/500.html"), 500


# ------------------------------------------------------------------------------
#                              UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
def send_verification_notification(portfolio, approved, admin_notes=None):
    """Send email notification about portfolio verification decision."""
    try:
        from ..utilities.email_sender import send_email

        editor = portfolio.editor
        if not editor or not editor.user:
            return False

        subject = f"Portfolio {'Approved' if approved else 'Rejected'}: {portfolio.title}"
        template = (
            "email/portfolio_approved"
            if approved
            else "email/portfolio_rejected"
        )

        send_email(
            [editor.user.emailAddress],
            subject,
            template,
            editor=editor,
            portfolio=portfolio,
            admin_notes=admin_notes,
        )

        return True

    except Exception as e:
        flask.current_app.logger.error(
            f"Failed to send verification notification: {str(e)}"
        )
        return False


def send_suspension_notification(user, reason=None):
    """Send email notification about account suspension."""
    try:
        from ..utilities.email_sender import send_email

        send_email(
            [user.emailAddress],
            "Account Suspended",
            "email/account_suspended",
            user=user,
            reason=reason,
        )

        return True

    except Exception as e:
        flask.current_app.logger.error(
            f"Failed to send suspension notification: {str(e)}"
        )
        return False


def log_admin_action(admin_id, action, target_type, target_id, details=None):
    """Log administrative actions for audit trail."""
    try:
        # In a production system, you might have an AdminLog model
        # For now, we'll just log to the application logger
        flask.current_app.logger.info(
            f"Admin {admin_id} performed {action} on {target_type} {target_id}. Details: {details}"
        )
        return True

    except Exception as e:
        flask.current_app.logger.error(f"Failed to log admin action: {str(e)}")
        return False
