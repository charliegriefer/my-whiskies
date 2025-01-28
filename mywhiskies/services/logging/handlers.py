import smtplib
from logging.handlers import SMTPHandler


class CustomSMTPHandler(SMTPHandler):
    """
    A custom SMTP handler that uses smtplib.SMTP_SSL on port 465.
    Needed because the built-in SMTPHandler doesn't fully support SSL-only servers.
    """

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
        self.credentials = credentials

    def emit(self, record):
        try:
            message = self.format(record)
            subject = f"My Whiskies Error: {record.levelname} at {record.pathname}"

            with smtplib.SMTP_SSL(
                self.mailhost, self.mailport, timeout=self.timeout
            ) as smtp:
                if self.credentials:
                    smtp.login(*self.credentials)
                msg = f"From: {self.fromaddr}\nTo: {', '.join(self.toaddrs)}\nSubject: {subject}\n\n{message}"
                smtp.sendmail(self.fromaddr, self.toaddrs, msg)
        except Exception:
            self.handleError(record)
