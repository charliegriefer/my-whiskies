import os
import logging
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=dotenv_path, verbose=True)


class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    BOTTLE_IMAGE_PATH = os.path.join(basedir, "app/static/bottles/")

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
    LOG_LEVEL = logging.DEBUG
    LOG_BACKTRACE = False

    # RECAPTCHA
    RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
    RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]

    @staticmethod
    def init_app(app):
        pass


class DevConfig(BaseConfig):
    DEBUG = os.environ["DEBUG"]


class ProdConfig(BaseConfig):
    # DATABASE
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MAIL
    MAIL_DEBUG = 0

    # LOGGING
    LOG_LEVEL = logging.INFO
    LOG_BACKTRACE = True


class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI_TEST"]
