import logging
import os
from logging.handlers import TimedRotatingFileHandler

from mywhiskies.services.logging.formatters import JsonFormatter
from mywhiskies.services.logging.handlers import CustomSMTPHandler

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"


def register_logging(app):
    if app.testing:
        return

    # set up file logging
    log_dir = app.config.get("LOG_DIR")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # text logging
    text_log = os.path.join(log_dir, "my-whiskies.log")
    text_handler = TimedRotatingFileHandler(
        text_log, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    text_handler.setLevel(app.config["LOG_LEVEL"])
    text_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    app.logger.addHandler(text_handler)

    # JSON structured logging
    json_log = os.path.join(log_dir, "my-whiskies.json.log")
    json_handler = TimedRotatingFileHandler(
        json_log, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    json_handler.setLevel(app.config["LOG_LEVEL"])
    json_handler.setFormatter(JsonFormatter())
    app.logger.addHandler(json_handler)

    # email handler
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
