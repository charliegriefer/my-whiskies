import logging
import os
from logging.handlers import TimedRotatingFileHandler

from mywhiskies.services.logging.handlers import CustomSMTPHandler

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"


def register_logging(app):
    if app.testing:
        return

    # Set up file logging
    log_dir = app.config.get("LOG_DIR")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "my-whiskies.log")
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
    file_handler.setLevel(app.config["LOG_LEVEL"])
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    app.logger.addHandler(file_handler)

    # Set up email notifications
    if app.config["MAIL_ADMINS"]:
        mail_handler = CustomSMTPHandler(
            mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            fromaddr=app.config["MAIL_USERNAME"],
            toaddrs=app.config["MAIL_ADMINS"],
            subject="My Whiskies Error",
            credentials=(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"]),
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        app.logger.addHandler(mail_handler)

    app.logger.setLevel(app.config["LOG_LEVEL"])
