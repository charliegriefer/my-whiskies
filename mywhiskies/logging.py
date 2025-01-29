import logging
import os
from logging.handlers import TimedRotatingFileHandler

from mywhiskies.services.logging.handlers import CustomSMTPHandler

LOG_FORMAT = "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"


def register_logging(app):
    # don't log tests
    if app.testing:
        return

    # development: only log main process
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    # production: only log from master process
    if not app.debug and os.getenv("GUNICORN_PARENT_PID") is not None:
        return

    # file logging setup (will only happen for master process)
    log_dir = app.config.get("LOG_DIR")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "my-whiskies.log")
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
    file_handler.setLevel(app.config["LOG_LEVEL"])
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    app.logger.addHandler(file_handler)

    # email error notifications
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

    # set overall logging level
    app.logger.setLevel(app.config["LOG_LEVEL"])

    if not app.debug:
        app.logger.handlers = [file_handler, mail_handler]

    app.logger.info("Logging Configured")
