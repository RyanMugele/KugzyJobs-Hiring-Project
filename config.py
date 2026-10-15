import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask security configuration options
    SECRET_KEY = os.environ.get("SECRET_KEY") or "#xpccEAN4nE_)FjZ9R-i"

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
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "Outback Kenya Lodge <info@jisortublow.co.ke>")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "info@jisortublow.co.ke")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "phOhsj3-")

    # Pesapal Payment Settings (Development)
    PESAPAL_CONSUMER_KEY = os.environ.get("PESAPAL_CONSUMER_KEY", "qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW")
    PESAPAL_CONSUMER_SECRET = os.environ.get("PESAPAL_CONSUMER_SECRET", "osGQ364R49cXKeOYSpaOnT++rHs=")
    PESAPAL_BASE_URL = os.environ.get("PESAPAL_BASE_URL", "https://cybqa.pesapal.com/pesapalv3")

    # Fetch Callbacks Settings
    API_SERVER_INDEX = (
        os.environ.get("API_SERVER_INDEX") or "http://127.0.0.1:5000"
    )

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEVELOPMENT_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "development.db")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory"
    )
    SECRET_KEY = "chdbvbjnhmkldfhgcavbxntkuymluv"


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    DB_NAME = os.environ.get("DB_NAME") or "freelance"
    DB_USERNAME = os.environ.get("DB_USERNAME") or "root"
    DB_HOST = os.environ.get("DB_HOST") or "localhost"
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or "MySQLXXX-123a8910"

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("PRODUCTION_DATABASE_URL")
        or f"mysql+mysqlconnector://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}"
        + f"/{DB_NAME}"
    )


    @classmethod
    def init_app(cls, app):
        pass


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
