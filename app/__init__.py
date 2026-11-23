import os
import flask
from flask_wtf.csrf import CSRFProtect
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
    try:
        user = db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None
    return user if user and user.isActive else None


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
    
    config[config_name].init_app(app)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY before starting production.")

    # Enable only behind the documented Render HTTPS proxy.
    if os.environ.get("TRUST_PROXY_HEADERS") == "1":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1, x_host=0, x_port=0)

    # Initialize extensions
    CSRFProtect(app)
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
    
    @app.get("/healthz")
    def healthz():
        from sqlalchemy import text
        try:
            db.session.execute(text("SELECT 1"))
            return {"status": "ok"}, 200
        except Exception:
            db.session.rollback()
            app.logger.exception("Database readiness check failed")
            return {"status": "unavailable"}, 503

    @app.before_request
    def reject_suspended_sessions():
        if flask_login.current_user.is_authenticated and not flask_login.current_user.isActive:
            flask_login.logout_user()
            flask.abort(403)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return app
