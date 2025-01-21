from flask import flash, url_for
from flask_login import login_user
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from werkzeug.urls import url_parse

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def get_user_by_username(username: str) -> User:
    stmt = (
        select(User)
        .options(joinedload(User.bottles))
        .filter_by(username=username, is_deleted=False)
    )
    with db.session() as session:
        user = session.execute(stmt).scalars().first()
        return user  # This user object is tied to the session used in this context


def validate_password(user: User, password: str) -> bool:
    return user is not None and user.check_password(password)


def check_email_confirmation(user: User) -> bool:
    if not user.email_confirmed:
        message = (
            "You have not yet confirmed your e-mail address. "
            "If you need the verification email re-sent, please "
            f"<a href='{url_for('auth.resend_register')}'>click here</a>."
        )
        flash(message, "danger")
        return False
    return True


def log_in_user(user: User, remember_me: bool) -> None:
    login_user(user, remember=remember_me)


def determine_next_page(user: User, next_page_param: str) -> str:
    if not next_page_param or url_parse(next_page_param).netloc != "":
        return url_for("core.main")
    return next_page_param
