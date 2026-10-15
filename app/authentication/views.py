import flask
from flask_login import current_user
from flask_login import login_required

from . import authentication
from .forms import LoginForm
from .forms import PasswordResetForm
from .forms import PasswordResetRequestForm
from .forms import CreatorRegistrationForm
from .forms import EditorRegistrationForm
from .forms import AdminRegistrationForm

from app import db
from ..models.user import User
from ..models.admin import Admin
from ..models.editor import Editor
from ..models.creator import Creator
from ..models.password_reset_token import PasswordResetToken


def redirect_after_login(dashboard_route, name):
    next_page = flask.request.args.get("next")
    if not next_page or not next_page.startswith("/"):
        next_page = flask.url_for(dashboard_route)

    flask.flash(f"Hello {name}. Welcome back!")
    return flask.redirect(next_page)


def redirect_based_on_role():
    """
    Redirect based on user type of the current user.
    """
    if current_user.userType == "creator":
        return flask.redirect(flask.url_for("creator.dashboard"))
    elif current_user.userType == "editor":
        return flask.redirect(flask.url_for("editor.dashboard"))
    elif current_user.userType == "admin":
        return flask.redirect(flask.url_for("admin.dashboard"))
    else:
        return flask.redirect(flask.url_for("authentication.login"))


@authentication.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login for all user types (creator, editor, admin).
    """
    # Redirect already logged-in users to their respective dashboards
    if current_user.is_authenticated:
        return redirect_based_on_role()

    form = LoginForm()

    if form.validate_on_submit():
        email = form.emailAddress.data.lower()
        password = form.password.data
        remember_me = form.remember_me.data

        # Find user by email address
        user = User.query.filter_by(emailAddress=email).first()

        # Attempt login and redirect based on user type
        if (
            user
            and user.login({"password": password, "remember_me": remember_me})[
                0
            ]
        ):
            dashboard_routes = {
                "creator": "creator.dashboard",
                "editor": "editor.dashboard",
                "admin": "admin.dashboard",
            }
            dashboard_route = dashboard_routes.get(
                user.userType, "authentication.login"
            )
            return redirect_after_login(dashboard_route, user.fullName)

        # Flash message if credentials are invalid
        flask.flash(
            "Invalid email address or password. Please try again.", "danger"
        )

    return flask.render_template("authentication/login.html", form=form)


# ------------------------------------------------------------------------------
#                                REGISTRATION                                 -
# ------------------------------------------------------------------------------
@authentication.route("/register/creator", methods=["GET", "POST"])
def creator_registration():
    """
    Handle content creator registration.
    """
    form = CreatorRegistrationForm()

    if form.validate_on_submit():
        try:
            # Create user account
            user_details = {
                "fullName": form.fullName.data,
                "emailAddress": form.emailAddress.data.lower(),
                "password": form.password.data,
                "userType": "creator",
            }

            user = User.registerAccount(user_details, isActive=True)

            # Create creator-specific record
            creator = Creator(
                userId=user.userId,
                contentType=form.contentType.data,
                platformFocus=form.platformFocus.data
                if form.platformFocus.data
                else None,
            )

            db.session.add(creator)
            db.session.commit()

            flask.flash(
                "Creator registration successful! You can now log in.",
                "success",
            )
            return flask.redirect(flask.url_for("authentication.login"))

        except IOError:
            db.session.rollback()
            flask.flash("Registration failed. Please try again.", "danger")

    return flask.render_template(
        "authentication/creator_registration.html", form=form
    )


@authentication.route("/register/editor", methods=["GET", "POST"])
def editor_registration():
    """
    Handle video editor registration.
    """
    form = EditorRegistrationForm()

    if form.validate_on_submit():
        try:
            # Create user account
            user_details = {
                "fullName": form.fullName.data,
                "emailAddress": form.emailAddress.data.lower(),
                "password": form.password.data,
                "userType": "editor",
            }

            user = User.registerAccount(user_details, isActive=True)

            # Parse hourly rate
            hourly_rate = None
            if form.hourlyRate.data:
                try:
                    hourly_rate = float(form.hourlyRate.data)
                except ValueError:
                    hourly_rate = None

            # Create editor-specific record
            editor = Editor(
                userId=user.userId,
                specializations=form.specializations.data,
                experienceLevel=form.experienceLevel.data
                if form.experienceLevel.data
                else None,
                hourlyRate=hourly_rate,
                isVerified=False,
            )

            db.session.add(editor)
            db.session.commit()

            flask.flash(
                "Editor registration successful! You can now log in and build your portfolio.",
                "success",
            )
            return flask.redirect(flask.url_for("authentication.login"))

        except Exception:
            db.session.rollback()
            flask.flash("Registration failed. Please try again.", "danger")

    return flask.render_template(
        "authentication/editor_registration.html", form=form
    )


@authentication.route("/register/admin", methods=["GET", "POST"])
def admin_registration():
    """
    Handle administrator registration (requires admin code).
    """
    form = AdminRegistrationForm()

    if form.validate_on_submit():
        try:
            # Create user account
            user_details = {
                "fullName": form.fullName.data,
                "emailAddress": form.emailAddress.data.lower(),
                "password": form.password.data,
                "userType": "admin",
            }

            user = User.registerAccount(user_details, isActive=True)

            # Create admin-specific record
            admin = Admin(
                userId=user.userId,
                roleDesignation=form.roleDesignation.data
                if form.roleDesignation.data
                else "moderator",
            )

            db.session.add(admin)
            db.session.commit()

            flask.flash(
                "Administrator registration successful! You can now log in.",
                "success",
            )
            return flask.redirect(flask.url_for("authentication.login"))

        except Exception:
            db.session.rollback()
            flask.flash("Registration failed. Please try again.", "danger")

    return flask.render_template(
        "authentication/admin_registration.html", form=form
    )


# ------------------------------------------------------------------------------
#                                SIGNING OUT                                  -
# ------------------------------------------------------------------------------
@authentication.route("/logout")
@login_required
def logout():
    """
    Handle user logout.
    """
    current_user.logout()
    flask.flash("You have been logged out successfully.")
    return flask.redirect(flask.url_for("authentication.login"))


# ------------------------------------------------------------------------------
#                           PASSWORD RESET REQUEST                            -
# ------------------------------------------------------------------------------
@authentication.route("/password-reset-request", methods=["GET", "POST"])
def password_reset_request():
    """
    Handle password reset request.
    """
    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        email_address = form.emailAddress.data.lower()

        # Find user by email address
        user = User.query.filter_by(emailAddress=email_address).first()

        if user:
            # Generate password reset token
            # reset_token = PasswordResetToken.generateToken(
            # user.userId, expiryHours=24
            # )

            # user.sendPasswordResetEmail(reset_token.token)

            flask.flash(
                "Password reset instructions have been sent to your email.",
                "info",
            )
        else:
            flask.flash("No account found with that email address.", "warning")

        return flask.redirect(
            flask.url_for("authentication.password_reset_request")
        )

    return flask.render_template(
        "authentication/password_reset_request.html", form=form
    )


# -----------------------------------------------------------------------------
#                               PASSWORD RESET                              -
# -----------------------------------------------------------------------------
@authentication.route("/password-reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    """
    Handle password reset with token validation.
    """
    # Redirect authenticated users
    if not current_user.is_anonymous:
        return redirect_based_on_role()

    # Validate token
    reset_token = PasswordResetToken.validateToken(token)
    if not reset_token:
        flask.flash("The password reset link is invalid or hxpired.", "danger")
        return flask.redirect(
            flask.url_for("authentication.password_reset_request")
        )

    form = PasswordResetForm()

    if form.validate_on_submit():
        try:
            # Update user password
            user = User.query.get(reset_token.userId)
            if user:
                # Update password using the BaseUser method
                user.updatePassword(form.password.data)

                # Mark token as used
                reset_token.markAsUsed()

                flask.flash(
                    "Your password has been updated successfully!", "success"
                )
                return flask.redirect(flask.url_for("authentication.login"))
            else:
                flask.flash("User account not found.", "danger")

        except Exception:
            db.session.rollback()
            flask.flash(
                "An error occurred while updating your password. Please try again.",
                "danger",
            )

    return flask.render_template(
        "authentication/password_reset.html", form=form
    )


# ------------------------------------------------------------------------------
#                           ACCOUNT REACTIVATION                              -
# ------------------------------------------------------------------------------
@authentication.route("/reactivate")
@login_required
def reactivate():
    """
    Handle account reactivation for suspended users.
    """
    if current_user.is_anonymous:
        return flask.redirect(flask.url_for("authentication.login"))

    if current_user.isActive:
        return redirect_based_on_role()

    return flask.render_template("authentication/account_suspended.html")


# ---------------------------------------------------------------------------
#                          HANDLE STALE SESSIONS                            -
# ---------------------------------------------------------------------------
@authentication.route("/reauthenticate")
@login_required
def reauthenticate():
    """
    Handle stale session reauthentication.
    """
    return flask.redirect(flask.url_for("authentication.logout"))


# ---------------------------------------------------------------------------
#                          REGISTRATION SUCCESS                             -
# ---------------------------------------------------------------------------
@authentication.route("/registration-success")
def registration_success():
    """
    Display registration success page.
    """
    return flask.render_template("authentication/registration_success.html")


# ---------------------------------------------------------------------------
#                          CHOOSE REGISTRATION TYPE                         -
# ---------------------------------------------------------------------------
@authentication.route("/register")
def choose_registration():
    """
    Display registration type selection page.
    """
    if current_user.is_authenticated:
        return redirect_based_on_role()

    return flask.render_template("authentication/choose_registration.html")
