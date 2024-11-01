from flask_mail import Message

from mywhiskies.extensions import mail


def send_email(subject, sender, recipients, text_body, html_body) -> None:
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
