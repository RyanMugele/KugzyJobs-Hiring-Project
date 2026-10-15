from flask import Blueprint, current_app

admin = Blueprint("admin", __name__)

from . import views, errors


@admin.app_context_processor
def global_variables():
    """
    Provide global variables for templates within the 'admin' blueprint.

    :return: A dictionary containing global variables to inject into templates.
    :rtype: dict
    """
    return dict(
        app_name=current_app.config.get(
            "ORGANIZATION_NAME", "Content Creator Platform"
        ),
    )
