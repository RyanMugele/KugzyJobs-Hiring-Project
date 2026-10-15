import flask
import flask_login
import flask_moment
import flask_migrate
import flask_mailman
import flask_sqlalchemy
from config import config

# Set endpoint for the login page
login_manager = flask_login.LoginManager()
login_manager.login_view = "authentication.login"

# Handle stale sessions
login_manager.refresh_view = "authentication.reauthenticate"
login_manager.needs_refresh_message = (
    "To protect your authentication, "
    + "please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    """
    Load user for Flask-Login based on user type stored in session.
    
    :param user_id: str - User ID from session
    :return: User object or None
    """
    from .models.user import User
    from .models.creator import Creator
    from .models.editor import Editor
    from .models.admin import Admin
    
    user_type = flask.session.get("user_type")
    
    if user_type == "creator":
        creator = Creator.query.get(int(user_id))
        return creator.user if creator else None
    elif user_type == "editor":
        editor = Editor.query.get(int(user_id))
        return editor.user if editor else None
    elif user_type == "admin":
        admin = Admin.query.get(int(user_id))
        return admin.user if admin else None
    else:
        # Fallback to base User model
        user = User.query.get(int(user_id))
        return user


# Initialize extensions
db = flask_sqlalchemy.SQLAlchemy()
mail = flask_mailman.Mail()
moment = flask_moment.Moment()
migrate = flask_migrate.Migrate()

def create_app(config_name="default"):
    """
    Initialize and configure the Flask application for Content Creator Platform.
    
    :param config_name: str - The name of the configuration class defined in config.py
    :return app: Flask - The configured Flask application instance
    """
    app = flask.Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    
    # Enable SSL redirection if configured
    if app.config.get("SSL_REDIRECT", False):
        from flask_sslify import SSLify
        SSLify(app)
    
    # Register main blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Register authentication blueprint
    from .authentication import authentication as authentication_blueprint
    app.register_blueprint(authentication_blueprint, url_prefix="/auth")
    
    # Register creator blueprint
    from .creator import creator as creator_blueprint
    app.register_blueprint(creator_blueprint, url_prefix="/creator")
    
    # Register editor blueprint
    from .editor import editor as editor_blueprint
    app.register_blueprint(editor_blueprint, url_prefix="/editor")
    
    # Register admin blueprint
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix="/admin")
    
    return app
