import logging
import os

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    ENV = "development"

    SECRET_KEY = os.environ["SECRET_KEY"]
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 1,
        "max_overflow": 0,
    }

    # MAIL
    MAIL_SERVER = os.environ["MAIL_SERVER"]
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ["MAIL_USERNAME"]
    MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]
    MAIL_SUBJECT_PREFIX = "[my-whiskies.online]"
    MAIL_SENDER = "Bartender <bartender@my-whiskies.online>"
    MAIL_ADMINS = ["bartender@my-whiskies.online", "charlie@griefer.com"]
    MAIL_DEBUG = 1

    # LOGGING
    LOG_LEVEL = os.environ["LOG_LEVEL"]
    LOG_BACKTRACE = False

    # RECAPTCHA
    RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
    RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]

    # AWS
    BOTTLE_IMAGE_S3_BUCKET = "my-whiskies-pics"
    BOTTLE_IMAGE_S3_KEY = "dev"
    BOTTLE_IMAGE_S3_URL = "https://my-whiskies-pics.s3-us-west-1.amazonaws.com"

    @staticmethod
    def init_app(app):
        pass


class DevConfig(BaseConfig):
    DEBUG = os.environ["DEBUG"]


class ProdConfig(BaseConfig):
    ENV = "production"

    # DATABASE
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MAIL
    MAIL_DEBUG = 0

    # LOGGING
    LOG_LEVEL = logging.INFO
    LOG_BACKTRACE = True

    # AWS
    BOTTLE_IMAGE_S3_KEY = "prod"


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI_TEST"]
    SQLALCHEMY_ENGINE_OPTIONS = {}

    WTF_CSRF_ENABLED = False  # Disable CSRF for testing purposes
    TESTING_RECAPTCHA_BYPASS = True  # Bypass ReCaptcha validation in tests
    LOG_LEVEL = logging.CRITICAL  # Suppress logging output during tests
