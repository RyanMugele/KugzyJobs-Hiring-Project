from flask import Blueprint
from flask import current_app

editor = Blueprint("editor", __name__)

from . import views, errors


@editor.app_context_processor
def global_variables():
    """
    Provide global variables for templates within the 'editor' blueprint.

    :return: A dictionary containing global variables to inject into templates.
    :rtype: dict
    """
    return dict(
        app_name=current_app.config.get(
            "ORGANIZATION_NAME", "Content Creator Platform"
        ),
    )
