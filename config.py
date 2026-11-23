import os
import secrets
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask security configuration options
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ADMIN_REGISTRATION_CODE = os.environ.get("ADMIN_REGISTRATION_CODE")
    PAYMENTS_ENABLED = False
    EMAIL_ENABLED = False
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # SQLAlchemy configuration options
    SSL_REDIRECT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SLOW_DB_QUERY_TIME = 0.5

    # Application configuration options
    ORGANIZATION_NAME = (
        os.environ.get("ORGANIZATION_NAME") or "KugzyJobs"
    )

    # File upload configuration options
    EDITORS_UPLOAD_PATH = os.path.join(basedir + "/app/static/img/editors/")
    CREATORS_UPLOAD_PATH = os.path.join(
        basedir + "/app/static/img/creators/"
    )
    UPLOAD_EXTENSIONS = [
        "jpg",
        "gif",
        "jpeg",
        "png",
        "avif",
        "webp",
        "mp4",
    ]

    # Mail connection configuration options
    MAIL_BACKEND = "smtp"
    MAIL_SERVER = "smtp.zoho.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_TIMEOUT = None

    # Mail Credentials Settings
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "KugzyJobs <noreply@example.com>")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Pesapal Payment Settings (Development)
    PESAPAL_CONSUMER_KEY = os.environ.get("PESAPAL_CONSUMER_KEY")
    PESAPAL_CONSUMER_SECRET = os.environ.get("PESAPAL_CONSUMER_SECRET")
    PESAPAL_BASE_URL = os.environ.get("PESAPAL_BASE_URL", "https://cybqa.pesapal.com/pesapalv3")

    # Fetch Callbacks Settings
    API_SERVER_INDEX = (
        os.environ.get("API_SERVER_INDEX") or "http://127.0.0.1:5000"
    )

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEVELOPMENT_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "development.db")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
    )
    SECRET_KEY = os.environ.get("TEST_SECRET_KEY", "testing-only-not-for-production")


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = os.environ.get("PRODUCTION_DATABASE_URL")
    DATA_DIR = os.environ.get("KUGZY_DATA_DIR")

    @classmethod
    def init_app(cls, app):
        from pathlib import Path
        if (not app.config.get("SECRET_KEY") or len(app.config["SECRET_KEY"]) < 32
                or app.config["SECRET_KEY"].startswith(("replace-with-", "testing-only"))):
            raise RuntimeError("Production requires a private SECRET_KEY of at least 32 characters.")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("Set PRODUCTION_DATABASE_URL to the persistent database.")
        if not cls.DATA_DIR or not Path(cls.DATA_DIR).is_absolute():
            raise RuntimeError("Set KUGZY_DATA_DIR to an absolute persistent directory.")
        root = Path(cls.DATA_DIR)
        root.mkdir(parents=True, exist_ok=True)
        # Keep legacy static image URLs while storing role image directories on disk.
        for role in ("editors", "creators"):
            target = root / "uploads" / role
            target.mkdir(parents=True, exist_ok=True)
            public = Path(app.static_folder) / "img" / role
            if public.is_symlink():
                if public.resolve() != target.resolve():
                    raise RuntimeError("Profile image directory points to another data location.")
            elif public.exists():
                if any(public.iterdir()):
                    raise RuntimeError("Move existing profile images to persistent storage first.")
                public.rmdir()
                public.symlink_to(target, target_is_directory=True)
            else:
                public.symlink_to(target, target_is_directory=True)
            app.config[role.upper()+"_UPLOAD_PATH"] = str(target)


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
