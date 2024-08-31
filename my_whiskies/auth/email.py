from flask import render_template, current_app
from my_whiskies.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email("[My Whiskies Online] Reset Your Password",
               sender=current_app.config["MAIL_SENDER"],
               recipients=[user.email],
               text_body=render_template("email/reset_password.txt", user=user, token=token),
               html_body=render_template("email/reset_password.html", user=user, token=token))


def send_registration_confirmation_email(user):
    token = user.get_mail_confirm_token()
    send_email("Please Confirm Your Email",
               sender=current_app.config["MAIL_SENDER"],
               recipients=[user.email],
               text_body=render_template("email/registration_confirmation.txt", user=user, token=token),
               html_body=render_template("email/registration_confirmation.html", user=user, token=token))
