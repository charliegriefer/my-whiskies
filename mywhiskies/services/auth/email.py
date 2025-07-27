from flask import abort, current_app, flash, render_template
from mywhiskies.models import User
from mywhiskies.services.email.email import send_email


def send_registration_confirmation_email(user: User, is_resend=False) -> None:
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


def send_password_reset_email(user: User) -> None:
    token = user.get_reset_password_token()
    try:
        send_email(
            "[My Whiskies Online] Reset Your Password",
            sender=current_app.config["MAIL_SENDER"],
            recipients=[user.email],
            text_body=render_template(
                "email/reset_password.txt", user=user, token=token
            ),
            html_body=render_template(
                "email/reset_password.html", user=user, token=token
            ),
        )
    except Exception:
        abort(500)
