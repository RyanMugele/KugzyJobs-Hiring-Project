from functools import wraps

import flask
from flask_login import current_user


def permission_required(permission):
    """
    Checks if the current user has the specified permission else raises 403
        error.

    :param permission: str - The required permission for accessing the
        decorated route.

    :return decorator: function - The decorated function.
    """

    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                flask.abort(403)
            return function(*args, **kwargs)

        return decorated_function

    return decorator


def user_type_validator(user_type):
    """
    Checks whether the current user is of the required user type.

    :param user_type: str - The required user type for accessing the decorated
        route.

    :return decorator: function - The decorated function.
    """

    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            if flask.session["user_type"] != user_type:
                flask.abort(403)
            return function(*args, **kwargs)

        return decorated_function

    return decorator


def account_approval_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.isActive:
            return view_func(*args, **kwargs)

        # Redirect to the email confirmation page
        return flask.redirect(flask.url_for("authentication.deactivated"))

    return wrapped_view
