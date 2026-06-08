from urllib.parse import urlparse

from flask import flash, url_for
from sqlalchemy import exists, func
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from mywhiskies.extensions import db
from mywhiskies.models import User, UserLogin


def get_user_by_username(username: str) -> User:
    stmt = (
        select(User)
        .options(joinedload(User.bottles))
        .filter(func.lower(User.username) == username.lower(), User.is_deleted == False)  # noqa: E712
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


def determine_next_page(user: User, next_page_param: str) -> str:
    if not next_page_param or urlparse(next_page_param).netloc != "":
        return url_for("core.main")
    return next_page_param


def is_new_ip(user_id: str, ip_address: str) -> bool:
    """Returns True if the user has prior logins but this IP has never been seen before."""
    has_any = db.session.execute(select(exists().where(UserLogin.user_id == user_id))).scalar()
    if not has_any:
        return False
    known = db.session.execute(
        select(exists().where(UserLogin.user_id == user_id, UserLogin.ip_address == ip_address))
    ).scalar()
    return not known
