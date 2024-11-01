from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import Markup, flash


def is_my_list(username, current_user) -> bool:
    return (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )


def handle_form_errors(form):
    # Get flash message and reset form if necessary
    errors_info = get_flash_msg(form)
    flash(Markup(errors_info["message"]), "danger")


def get_flash_msg(form) -> dict:
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


def set_cookie_expiration(response, cookie_name, value, years=1):
    response.set_cookie(
        cookie_name,
        value=value,
        expires=datetime.now() + relativedelta(years=years),
    )
