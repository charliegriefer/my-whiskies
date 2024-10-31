from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, logout_user

from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.auth.forms import LoginForm
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    get_user_by_username,
    log_in_user,
    validate_password,
)


@auth.route("/login", methods=["GET", "POST"], strict_slashes=False)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.home", username=current_user.username))

    form = LoginForm()

    if form.validate_on_submit():
        user = get_user_by_username(form.username.data)

        if not validate_password(user, form.password.data):
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


@auth.route("/logout", strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for("core.index"))
