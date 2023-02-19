import os
import logging
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


load_dotenv(dotenv_path=dotenv_path, verbose=True)

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.environ["SECRET_KEY"]
    BOTTLE_IMAGE_PATH = os.path.join(basedir, "app/static/bottles/")

    # DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # MAIL
    MAIL_SERVER = os.environ["MAIL_SERVER"]
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ["MAIL_USERNAME"]
    MAIL_PASSWORD = os.environ["MAIL_PASSWORD"]
    MAIL_SUBJECT_PREFIX = "[my-whiskies.online]"
    MAIL_SENDER = "Bartender <bartender@my-whiskies.online>"
    MAIL_ADMINS = ["bartender@my-whiskies.online"]
    MAIL_DEBUG = 1

    # LOGGING
    LOG_LEVEL = logging.DEBUG
    LOG_BACKTRACE = False

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
    LOG_LEVEL = logging.ERROR
    LOG_BACKTRACE = True

    @classmethod
    def init_app(cls, app):
        BaseConfig.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, "MAIL_USERNAME", None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, "MAIL_USE_TLS", None):
                secure = ()
        mail_handler = SMTPHandler(mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
                                   fromaddr=cls.MAIL_SENDER,
                                   toaddrs=cls.MAIL_ADMINS,
                                   subject=cls.MAIL_SUBJECT_PREFIX + " Application Error",
                                   credentials=credentials,
                                   secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
