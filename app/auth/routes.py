from datetime import datetime
from textwrap import dedent

from flask import current_app, flash, redirect, render_template, request, url_for, Markup
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from wtforms.fields.core import Label

from app.auth import auth_blueprint
from app.auth.email import send_password_reset_email, send_registration_confirmation_email
from app.auth import forms
from app.extensions import db
from app.models import User


@auth_blueprint.route("/login", methods=["GET", "POST"], strict_slashes=False)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    form = forms.LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.one_or_404(db.select(User).filter_by(username=form.username.data, is_deleted=False))
        if user is None or not user.check_password(form.password.data):
            flash("Incorrect username or password!", "danger")
            return redirect(url_for("auth.login"))
        if not user.email_confirmed:
            message = "You have not yet confirmed your e-mail address.  "
            message += "If you need the verification email re-sent, please "
            message += Markup(f"<a href='{url_for('auth.resend_register')}'>click here</a>.")
            flash(message, "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.home", username=user.username.lower())
        return redirect(next_page)
    return render_template("auth/login.html", title="My Whiskies Online: Log In", form=form)


@auth_blueprint.route("/logout", strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_blueprint.route("/register", methods=["GET", "POST"], strict_slashes=False)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    form = forms.RegistrationForm()
    terms_label = Markup(f"I agree to the terms of <a href=\"{url_for('main.terms')}\">Terms of Service</a>.")
    form.agree_terms.label = Label("agree_terms", terms_label)
    if request.method == "POST" and form.validate_on_submit():
        # print(form.recaptcha.data)
        user_in = User()

        user_in.username = form.username.data.strip()
        user_in.email = form.email.data.strip()
        user_in.email_confirmed = False

        user_in.set_password(form.password.data)

        db.session.add(user_in)
        db.session.commit()
        send_registration_confirmation_email(user_in)
        flash(Markup(dedent("""\
            <p>Check your e-mail for further instructions.</p>
            <p>If you don't receive an e-mail within an hour:</p>
            <ul>
                <li>Check your spam folder</li>
                <li>Consider whitelisting the domain my-whiskies.online</li>
            </ul>""")), "info")
        return redirect(url_for("auth.login"))
    if form.errors:
        m = get_flash_msg(form)
        flash(m.get("message"), "danger")
        if m.get("reset_errors"):
            form = forms.RegistrationForm()
            terms_label = Markup(f"I agree to the terms of <a href=\"{url_for('main.terms')}\">Terms of Service</a>.")
            form.agree_terms.label = Label("agree_terms", terms_label)
    return render_template("auth/register.html",
                           title="My Whiskies Online: Register",
                           has_captcha=True,
                           form=form,
                           recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"])


@auth_blueprint.route("/confirm_register/<token>", methods=["GET", "POST"], strict_slashes=False)
def confirm_register(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    user = User.verify_mail_confirm_token(token)
    if not user:
        link = f"<a href=\"{url_for('auth.resend_register')}\">click here</a>"
        flash(Markup(f"There was a problem confirming your registration. Please {link} to re-send the email."),
              "danger")
        return redirect(url_for("auth.login"))

    user.email_confirmed = True
    user.email_confirm_date = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    flash("Your email has been verified. You can now login to your account", "success")
    return redirect(url_for("auth.login"))


@auth_blueprint.route("/resend_register", methods=["GET", "POST"], strict_slashes=False)
def resend_register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    form = forms.ResendRegEmailForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.session.query(User).filter(User.email == form.email.data).one_or_none()
        if user:
            send_registration_confirmation_email(user)
            flash(f"A new registration verification e-mail has been sent to {form.email.data}", "info")
            return redirect(url_for("auth.login"))
        else:
            flash(f"{form.email.data} is not a valid e-mail with My Whiskies Online.", "danger")
            return redirect(url_for("auth.resend_register"))
    return render_template("auth/resend_register.html",
                           title="My Whiskies Online: Re-Send Registration Confirmation",
                           form=form)


@auth_blueprint.route("/reset_password_request", methods=["GET", "POST"], strict_slashes=False)
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    form = forms.ResetPasswordRequestForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_deleted=False).first()
        if user:
            send_password_reset_email(user)
        flash(Markup(dedent("""\
                    <p>Check your email for instructions on how to reset your password.</p>
                    <p>If you don't receive an e-mail within an hour:</p>
                    <ul>
                        <li>Check your spam folder</li>
                        <li>Consider whitelisting the domain my-whiskies.online</li>
                    </ul>""")), "info")
        return redirect(url_for("auth.login"))

    if form.errors:
        m = get_flash_msg(form)
        flash(m.get("message"), "danger")
    return render_template("auth/reset_password_request.html",
                           title="My Whiskies Online: Forgot Password",
                           has_captcha=True,
                           form=form,
                           recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"])


@auth_blueprint.route("/reset_password/<token>", methods=["GET", "POST"], strict_slashes=False)
def reset_password(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("main.home", username=current_user.username))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("main.index"))
    form = forms.ResetPWForm()
    if request.method == "POST" and form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", title="My Whiskies Online: Reset Password", form=form)


def get_flash_msg(form) -> dict:
    reset_errors = False
    if "recaptcha" in form.errors:
        flash_msg = form.errors["recaptcha"][0]
        reset_errors = True
    else:
        flash_msg = "Please correct the following issue(s): "
        flash_msg += "<ul>"
        for _, v in form.errors.items():
            for e in v:
                flash_msg += f"<li>{e}</li>"
        flash_msg += "</ul>"

    return {"message": flash_msg, "reset_errors": reset_errors}
