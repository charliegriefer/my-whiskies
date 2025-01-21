from datetime import datetime
from typing import Optional

from flask import Markup, flash, url_for

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def verify_confirmation_token(token: str) -> Optional[User]:
    return User.verify_mail_confirm_token(token)


def find_user_by_email(email: str) -> Optional[User]:
    stmt = db.select(User).filter(User.email == email.strip())
    return db.session.execute(stmt).first()


def register_user(username: str, email: str, password: str) -> User:
    user = User(username=username.strip(), email=email.strip(), email_confirmed=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def flash_registration_instructions() -> None:
    flash(
        Markup(
            """<p>Check your e-mail for further instructions.</p>
           <p>If you don't receive an e-mail within an hour:</p>
           <ul><li>Check your spam folder</li><li>Consider whitelisting the domain my-whiskies.online</li></ul>"""
        ),
        "info",
    )


def flash_email_verification_error() -> None:
    link = f"<a href=\"{url_for('auth.resend_register')}\">click here</a>"
    flash(
        Markup(
            f"There was a problem confirming your registration. Please {link} to re-send the email."
        ),
        "danger",
    )


def flash_email_verification_success() -> None:
    # Flash a success message when email is confirmed
    flash("Your email has been verified. You can now login to your account", "success")


def confirm_user_email(user: User) -> None:
    user.email_confirmed = True
    user.email_confirm_date = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
