from flask import current_app, redirect, render_template, request, url_for
from flask_login import current_user

from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.auth.forms import ResetPasswordRequestForm, ResetPWForm
from mywhiskies.services.auth.email import send_password_reset_email
from mywhiskies.services.auth.password import (
    find_user_for_password_reset,
    flash_password_reset_instructions,
    flash_password_reset_success,
    reset_user_password,
    verify_reset_password_token,
)


@auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    form = ResetPasswordRequestForm()

    if form.validate_on_submit():
        user = find_user_for_password_reset(form.email.data)
        if user:
            send_password_reset_email(user)
            current_app.logger.info(
                "Password reset requested",
                extra={"user": user.email, "ip": request.remote_addr},
            )
        flash_password_reset_instructions()
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password_request.html",
        title="My Whiskies Online: Forgot Password",
        form=form,
        has_captcha=True,
        recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"],
    )


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    user = verify_reset_password_token(token)
    if not user:
        return redirect(url_for("core.main"))

    form = ResetPWForm()
    if form.validate_on_submit():
        reset_user_password(user, form.password.data)
        flash_password_reset_success()
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html",
        title="My Whiskies Online: Reset Password",
        form=form,
        has_captcha=True,
        recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"],
    )
