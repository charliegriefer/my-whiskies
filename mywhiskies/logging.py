import logging
import os
import smtplib
from logging.handlers import SMTPHandler, TimedRotatingFileHandler


def register_logging(app):
    log_dir = os.getenv("LOG_DIR")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging configuration: don't log when testing, and only log once when running the app.
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        log_file = os.path.join(log_dir, "my-whiskies.log")
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
        file_handler.setLevel(os.getenv("LOG_LEVEL"))
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        app.logger.addHandler(file_handler)

    if not app.testing and app.config.get("MAIL_ADMINS"):

        class CustomSMTPHandler(SMTPHandler):
            def __init__(
                self,
                mailhost,
                fromaddr,
                toaddrs,
                subject,
                credentials=None,
                secure=None,
                timeout=5.0,
            ):
                super().__init__(
                    mailhost, fromaddr, toaddrs, subject, credentials, secure, timeout
                )
                self.credentials = (
                    credentials  # Explicitly set credentials as an instance attribute
                )
                print(
                    f"CustomSMTPHandler initialized with credentials: {self.credentials}"
                )

            def emit(self, record):
                try:
                    message = self.format(record)
                    subject = (
                        f"My Whiskies Error: {record.levelname} at {record.pathname}"
                    )

                    with smtplib.SMTP_SSL(
                        self.mailhost, self.mailport, timeout=self.timeout
                    ) as smtp:
                        if self.credentials:
                            smtp.login(*self.credentials)
                        msg = f"From: {self.fromaddr}\nTo: {', '.join(self.toaddrs)}\nSubject: {subject}\n\n{message}"
                        smtp.sendmail(self.fromaddr, self.toaddrs, msg)
                except Exception:
                    self.handleError(record)

        mail_handler = CustomSMTPHandler(
            mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            fromaddr=app.config["MAIL_USERNAME"],
            toaddrs=app.config["MAIL_ADMINS"],
            subject="My Whiskies Error",
            credentials=(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"]),
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        app.logger.addHandler(mail_handler)

    app.logger.setLevel(os.getenv("LOG_LEVEL"))
    app.logger.info("App startup")
