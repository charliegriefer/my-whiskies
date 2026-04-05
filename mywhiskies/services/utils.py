from flask import flash
from flask_wtf import FlaskForm as Form
from markupsafe import Markup

from mywhiskies.models import User


def is_my_list(username: str, current_user: User) -> bool:
    # is the current user logged in and viewing their own bottles?
    return (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )


def handle_form_errors(form: Form) -> None:
    # Get flash message and reset form if necessary
    errors_info = get_flash_msg(form)
    flash(Markup(errors_info["message"]), "danger")


def get_flash_msg(form: Form) -> dict:
    reset_errors = False
    if "recaptcha" in form.errors:
        flash_msg = form.errors["recaptcha"][0]
        reset_errors = True
    else:
        flash_msg = "Please correct the following issue(s): "
        flash_msg += "<ul>"
        for _, v in form.errors.items():
            for e in v:
                flash_msg += f"<li>{e}</li>"
        flash_msg += "</ul>"

    return {"message": flash_msg, "reset_errors": reset_errors}
