from flask import current_app, flash, render_template
from flask_mail import Message

from mywhiskies.extensions import mail


def send_email(subject, sender, recipients, text_body, html_body) -> None:
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_registration_confirmation_email(user, is_resend=False) -> None:
    token = user.get_mail_confirm_token()
    send_email(
        "Please Confirm Your Email",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[user.email],
        text_body=render_template(
            "email/registration_confirmation.txt", user=user, token=token
        ),
        html_body=render_template(
            "email/registration_confirmation.html", user=user, token=token
        ),
    )
    if is_resend:
        flash(
            f"A new registration verification e-mail has been sent to {user.email}",
            "info",
        )


def send_password_reset_email(user) -> None:
    token = user.get_reset_password_token()
    send_email(
        "[My Whiskies Online] Reset Your Password",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[user.email],
        text_body=render_template("email/reset_password.txt", user=user, token=token),
        html_body=render_template("email/reset_password.html", user=user, token=token),
    )
