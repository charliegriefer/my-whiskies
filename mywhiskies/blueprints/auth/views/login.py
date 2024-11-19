from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, logout_user
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.auth.forms import LoginForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    log_in_user,
    validate_password,
)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.home", username=current_user.username))

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
            flash("Incorrect username or password!", "danger")
            return redirect(url_for("auth.login"))

        if not check_email_confirmation(user):
            return redirect(url_for("auth.login"))

        log_in_user(user, form.remember_me.data)
        next_page = determine_next_page(user, request.args.get("next"))
        return redirect(next_page)

    return render_template(
        "auth/login.html", title="My Whiskies Online: Log In", form=form
    )


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("core.index"))
