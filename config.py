import logging
import os

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    ENV = "development"

    SECRET_KEY = os.environ["SECRET_KEY"]
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    MAX_FILE_UPLOAD_MB = 10
    MAX_FILE_UPLOAD_BYTES = MAX_FILE_UPLOAD_MB * 1024 * 1024

    # ----------------------------------------------------------------------
    # DATABASE
    # ----------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Hardened SQLAlchemy engine options
    # These prevent stale connections, increase resilience under load,
    # and give Gunicorn workers enough room to operate safely.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,  # how many connections per worker
        "max_overflow": 10,  # how many temporary extra connections
        "pool_pre_ping": True,  # validates connection before use
        "pool_recycle": 1800,  # reconnect every 30 minutes
    }

    # ----------------------------------------------------------------------
    # MAIL
    # ----------------------------------------------------------------------
    MAIL_SERVER = os.environ["MAIL_SERVER"]
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ["MAIL_USERNAME"]
    MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]
    MAIL_SUBJECT_PREFIX = "[my-whiskies.online]"
    MAIL_SENDER = "Bartender <bartender@my-whiskies.online>"
    MAIL_ADMINS = ["bartender@my-whiskies.online", "charlie@griefer.com"]
    MAIL_DEBUG = 1

    # ----------------------------------------------------------------------
    # LOGGING
    # ----------------------------------------------------------------------
    LOG_LEVEL = os.environ["LOG_LEVEL"]
    LOG_BACKTRACE = False
    LOG_DIR = os.environ["LOG_DIR"]

    # ----------------------------------------------------------------------
    # RECAPTCHA
    # ----------------------------------------------------------------------
    RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
    RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]

    # ----------------------------------------------------------------------
    # AWS
    # ----------------------------------------------------------------------
    BOTTLE_IMAGE_S3_BUCKET = "my-whiskies-pics"
    BOTTLE_IMAGE_S3_KEY = "dev"
    BOTTLE_IMAGE_S3_URL = "https://my-whiskies-pics.s3-us-west-1.amazonaws.com"

    @staticmethod
    def init_app(app):
        pass


class DevConfig(BaseConfig):
    DEBUG = os.environ["DEBUG"]

    # Smaller pool in dev is fine
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 2,
        "max_overflow": 2,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


class ProdConfig(BaseConfig):
    ENV = "production"

    # Turn off debugging-related DB chatter
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_DEBUG = 0

    LOG_LEVEL = logging.INFO
    LOG_BACKTRACE = True

    BOTTLE_IMAGE_S3_KEY = "prod"


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI_TEST"]

    # Tests don't need connection pools
    SQLALCHEMY_ENGINE_OPTIONS = {}

    WTF_CSRF_ENABLED = False
    TESTING_RECAPTCHA_BYPASS = True
    LOG_LEVEL = logging.CRITICAL
