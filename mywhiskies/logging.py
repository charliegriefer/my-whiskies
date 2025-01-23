import logging
import os
from logging.handlers import TimedRotatingFileHandler


def register_logging(app):
    log_dir = os.getenv("LOG_DIR")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging configuration: don't log when testing, and only log once when running the app.
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        log_file = os.path.join(log_dir, "my-whiskies.log")
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
        file_handler.setLevel(os.getenv("LOG_LEVEL", logging.INFO))
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        app.logger.addHandler(file_handler)

    app.logger.setLevel(os.getenv("LOG_LEVEL", logging.INFO))
    app.logger.info("App startup")
