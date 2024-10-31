from textwrap import dedent
from typing import Optional

from flask import Markup, flash

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def find_user_for_password_reset(email) -> Optional[User]:
    return (
        db.session.execute(db.select(User).filter_by(email=email, is_deleted=False))
        .scalars()
        .first()
    )


def verify_reset_password_token(token) -> Optional[User]:
    # Verifies the password reset token and returns the user if valid
    return User.verify_reset_password_token(token)


def reset_user_password(user, new_password) -> None:
    # Sets the new password for the user and commits the change
    user.set_password(new_password)
    db.session.commit()


def flash_password_reset_instructions() -> None:
    # Flash message to instruct the user to check email for further instructions
    flash(
        Markup(
            dedent(
                """\
                <p>Check your email for instructions on how to reset your password.</p>
                <p>If you don't receive an e-mail within an hour:</p>
                <ul>
                    <li>Check your spam folder</li>
                    <li>Consider whitelisting the domain my-whiskies.online</li>
                </ul>"""
            )
        ),
        "info",
    )


def flash_password_reset_success() -> None:
    # Flash a success message after password reset
    flash("Your password has been reset.", "success")
