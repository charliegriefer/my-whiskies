from smtplib import SMTPRecipientsRefused

from flask_mail import Message

from my_whiskies import mail


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    try:
        mail.send(msg)
    except SMTPRecipientsRefused:
        pass
