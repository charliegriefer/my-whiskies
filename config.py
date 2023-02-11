import os
from dotenv import load_dotenv
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = "c81f01e4fda60483ceab507f089cb628ba69b7d30dee78c6ae1fa483e7f0738f"
    SQLALCHEMY_DATABASE_URI = "mysql://root:password@localhost/my-whiskies"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BOTTLE_IMAGE_PATH = os.path.join(basedir, "app/static/bottles/")

    # MAIL
    MAIL_SERVER = "mail.privateemail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = "bartender@my-whiskies.online"
    MAIL_PASSWORD = "AEA9fvb4keg4tup!qud"
    MAIL_SUBJECT_PREFIX = "[my-whiskies.online]"
    MAIL_SENDER = "Bartender <bartender@my-whiskies.online>"
    MAIL_ADMINS = ["bartener@my-whiskies.online"]
    MAIL_SYNC = True

    # LOGGING
    LOG_LEVEL = 40

    @staticmethod
    def init_app(app):
        pass


class DevConfig(BaseConfig):
    FLASK_ENV = "development"

    # LOGGING
    LOGFILE = "logs/partnerup.log"
    LOG_BACKTRACE = True
    LOG_LEVEL = 10


class ProdConfig(BaseConfig):
    FLASK_ENV = "production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SYNC = False

    # LOGGING
    LOGFILE = "logs/partnerup.log"
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
