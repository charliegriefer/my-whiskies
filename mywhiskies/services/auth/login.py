from flask import flash, url_for
from flask_login import login_user
from werkzeug.urls import url_parse

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def get_user_by_username(username):
    return db.one_or_404(db.select(User).filter_by(username=username, is_deleted=False))


def validate_password(user, password):
    return user.check_password(password)


def check_email_confirmation(user):
    if not user.email_confirmed:
        message = (
            "You have not yet confirmed your e-mail address. "
            "If you need the verification email re-sent, please "
            f"<a href='{url_for('auth.resend_register')}'>click here</a>."
        )
        flash(message, "danger")
        return False
    return True


def log_in_user(user, remember_me):
    login_user(user, remember=remember_me)


def determine_next_page(user, next_page_param):
    if not next_page_param or url_parse(next_page_param).netloc != "":
        return url_for("core.home", username=user.username)
    return next_page_param
