from flask import abort, current_app, flash, render_template

from mywhiskies.models import User
from mywhiskies.services.email.email import send_email


def send_registration_confirmation_email(user: User, is_resend=False) -> None:
    token = user.get_mail_confirm_token()
    send_email(
        "Please Confirm Your Email",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[user.email],
        text_body=render_template("email/registration_confirmation.txt", user=user, token=token),
        html_body=render_template("email/registration_confirmation.html", user=user, token=token),
    )
    if is_resend:
        flash(
            f"A new registration verification e-mail has been sent to {user.email}",
            "info",
        )


def send_new_login_alert(user: User, ip_address: str) -> None:
    send_email(
        "[My Whiskies Online] New Login From an Unrecognized Location",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[user.email],
        text_body=render_template("email/new_login_alert.txt", user=user, ip_address=ip_address),
        html_body=render_template("email/new_login_alert.html", user=user, ip_address=ip_address),
    )


def send_email_change_confirmation(user: User, new_email: str) -> None:
    token = user.get_email_change_token(new_email)
    send_email(
        "[My Whiskies Online] Confirm Your New Email Address",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[new_email],
        text_body=render_template("email/email_change_confirmation.txt", user=user, token=token),
        html_body=render_template("email/email_change_confirmation.html", user=user, token=token),
    )


def send_inactive_account_warning(user: User, grace_days: int) -> None:
    send_email(
        "[My Whiskies Online] Your Account Will Be Deleted Due to Inactivity",
        sender=current_app.config["MAIL_SENDER"],
        recipients=[user.email],
        text_body=render_template("email/inactive_warning.txt", user=user, grace_days=grace_days),
        html_body=render_template("email/inactive_warning.html", user=user, grace_days=grace_days),
    )


def send_password_reset_email(user: User) -> None:
    token = user.get_reset_password_token()
    try:
        send_email(
            "[My Whiskies Online] Reset Your Password",
            sender=current_app.config["MAIL_SENDER"],
            recipients=[user.email],
            text_body=render_template("email/reset_password.txt", user=user, token=token),
            html_body=render_template("email/reset_password.html", user=user, token=token),
        )
    except Exception:
        abort(500)
