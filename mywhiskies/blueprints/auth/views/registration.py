from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user

from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.auth.forms import RegistrationForm, ResendRegEmailForm
from mywhiskies.services import utils
from mywhiskies.services.auth.email import send_registration_confirmation_email
from mywhiskies.services.auth.registration import (
    confirm_user_email,
    find_user_by_email,
    flash_email_verification_error,
    flash_email_verification_success,
    flash_registration_instructions,
    register_user,
    verify_confirmation_token,
)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
        )
        send_registration_confirmation_email(user)
        flash_registration_instructions()
        return redirect(url_for("auth.login"))

        current_app.logger.info(f"Form validation errors: {form.errors}")
        utils.handle_form_errors(form)

    return render_template(
        "auth/register.html",
        title="My Whiskies Online: Register",
        has_captcha=True,
        form=form,
        recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"],
    )


@auth.route("/confirm_register/<token>", methods=["GET", "POST"])
def confirm_register(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    user = verify_confirmation_token(token)
    if not user:
        flash_email_verification_error()
        return redirect(url_for("auth.login"))

    confirm_user_email(user)
    flash_email_verification_success()
    return redirect(url_for("auth.login"))


@auth.route("/resend_register", methods=["GET", "POST"])
def resend_register():
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    form = ResendRegEmailForm()
    if form.validate_on_submit():
        user = find_user_by_email(form.email.data)
        if not user:
            flash("No user found with that email address.", "danger")
            return redirect(url_for("auth.resend_register"))

        if user.email_confirmed:
            flash("This email address has already been confirmed.", "info")
            return redirect(url_for("auth.login"))

        send_registration_confirmation_email(user, is_resend=True)
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/resend_register.html",
        title="My Whiskies Online: Re-Send Registration Confirmation",
        form=form,
        has_captcha=True,
        recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"],
    )
