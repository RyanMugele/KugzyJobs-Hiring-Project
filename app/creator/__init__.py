from flask import Blueprint
from flask import current_app

from datetime import datetime

creator = Blueprint("creator", __name__)
from . import views, errors


@creator.app_context_processor
def global_variables():
    """
    Provide global variables for templates within the 'creator' blueprint.

    :return: A dictionary containing global variables to inject into templates.
    :rtype: dict

    :params: None
    """
    return dict(
        app_name=current_app.config.get(
            "ORGANIZATION_NAME", "Content Creator Platform"
        ),
        datetime=datetime,
    )
