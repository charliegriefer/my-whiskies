from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from mywhiskies.blueprints.auth import auth
from mywhiskies.extensions import db
from mywhiskies.forms.auth import LoginForm
from mywhiskies.models import User
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    validate_password,
)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.main"))

    form = LoginForm()

    if form.validate_on_submit():
        user = (
            (
                db.session.execute(
                    select(User)
                    .filter_by(username=form.username.data, is_deleted=False)
                    .options(joinedload(User.distilleries))
                )
            )
            .scalars()
            .first()
        )

        if user is None or not validate_password(user, form.password.data):
            current_app.logger.warning(
                f"Invalid login attempt for username '{form.username.data}' "
                f"from IP {request.remote_addr}"
            )
            flash("The username and password combination is not recognized.", "danger")
            return redirect(url_for("auth.login"))

        if not check_email_confirmation(user):
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)

        next_page = determine_next_page(user, request.args.get("next"))
        return redirect(next_page)

    return render_template(
        "auth/login.html",
        title="My Whiskies Online: Log In",
        has_captcha=True,
        form=form,
        recaptcha_public_key=current_app.config["RECAPTCHA_PUBLIC_KEY"],
    )


@auth.route("/logout")
def logout():
    current_app.logger.info(f"User {current_user.username} logged out")
    logout_user()
    return redirect(url_for("core.main"))
