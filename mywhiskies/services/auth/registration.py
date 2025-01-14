from datetime import datetime

from flask import Markup, flash, url_for
from wtforms.fields import Label

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def verify_confirmation_token(token):
    return User.verify_mail_confirm_token(token)


def find_user_by_email(email):
    # Finds a user by email
    return db.session.execute(db.select(User).filter(User.email == email)).scalar()


def initialize_registration_form(form):
    terms_label = Markup(
        f"I agree to the terms of <a href=\"{url_for('core.terms')}\">Terms of Service</a>"
    )
    form.agree_terms.label = Label("agree_terms", terms_label)
    return form


def register_user(username, email, password):
    user = User(username=username.strip(), email=email.strip(), email_confirmed=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def flash_registration_instructions():
    flash(
        Markup(
            """<p>Check your e-mail for further instructions.</p>
           <p>If you don't receive an e-mail within an hour:</p>
           <ul><li>Check your spam folder</li><li>Consider whitelisting the domain my-whiskies.online</li></ul>"""
        ),
        "info",
    )


def flash_email_verification_error():
    link = f"<a href=\"{url_for('auth.resend_register')}\">click here</a>"
    flash(
        Markup(
            f"There was a problem confirming your registration. Please {link} to re-send the email."
        ),
        "danger",
    )


def flash_email_verification_success():
    # Flash a success message when email is confirmed
    flash("Your email has been verified. You can now login to your account", "success")


def confirm_user_email(user):
    user.email_confirmed = True
    user.email_confirm_date = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
