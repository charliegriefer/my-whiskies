from datetime import datetime

from flask import flash, redirect, render_template, request, url_for, Markup
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app.extensions import db
from app.auth import auth_blueprint
from app.auth.email import send_password_reset_email, send_registration_confirmation_email
from app.auth.forms import LoginForm, RegistrationForm, ResendRegEmailForm, ResetPWForm, ResetPasswordRequestForm
from app.models.user import User


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, is_deleted=False).first()
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
            next_page = url_for("main.home")
        return redirect(next_page)
    return render_template("auth/login.html", title="Log In", form=form)


@auth_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()

    if request.method == "POST" and form.validate_on_submit():
        # TODO: Pycharm doesn't like this instantiation, but it is correct!
        user = User(username=form.username.data,
                    email=form.email.data,
                    email_confirmed=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        send_registration_confirmation_email(user)
        flash("Please check your e-mail for further instructions.", "info")
        return redirect(url_for("auth.login"))
    if form.errors:
        flash(get_flash_msg(form), "danger")
    return render_template("auth/register.html", title="Register", form=form)


@auth_blueprint.route("/confirm_register/<token>", methods=["GET", "POST"])
def confirm_register(token: str):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
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


@auth_blueprint.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordRequestForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, is_deleted=False).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for instructions on how to reset your password.", "info")
        return redirect(url_for("auth.login"))

    if form.errors:
        flash("oops", "danger")
    return render_template("auth/reset_password_request.html", title="Forgot Password?", form=form)


def get_flash_msg(form) -> str:
    flash_msg = "Please correct the following issue(s): <ul>"
    for _, v in form.errors.items():
        for e in v:
            flash_msg += f"<li>{e}</li>"
    flash_msg += "</ul>"
    return flash_msg
