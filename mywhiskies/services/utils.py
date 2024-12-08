import random
from datetime import datetime
from typing import Union

from dateutil.relativedelta import relativedelta
from flask import Markup, flash, make_response, render_template, request
from flask.wrappers import Response

from mywhiskies.blueprints.bottle.models import BottleTypes
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User


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


def prep_datatables(
    entity: Union[Distillery, User], current_user: User, request: request
) -> Response:
    if type(entity) is Distillery:
        user = entity.user
        all_bottles = entity.bottles
    else:
        user = entity
        all_bottles = user.bottles

    killed_bottles = [b for b in all_bottles if b.date_killed]
    private_bottles = [b for b in all_bottles if b.is_private]
    if request.method == "POST":
        active_bottle_types = request.form.getlist("bottle_type")

        if len(active_bottle_types):
            bottles_to_list = [
                b for b in all_bottles if b.type.name in active_bottle_types
            ]
            if bool(int(request.form.get("random_toggle"))):
                if len(bottles_to_list) > 0:
                    unkilled_bottles = [b for b in bottles_to_list if not b.date_killed]
                    bottles_to_list = [random.choice(unkilled_bottles)]
        else:
            bottles_to_list = []
    else:
        active_bottle_types = [bt.name for bt in BottleTypes]
        if user == current_user:
            bottles_to_list = all_bottles
        else:
            bottles_to_list = [
                bottle for bottle in all_bottles if not bottle.is_private
            ]

    _is_my_list = is_my_list(user.username, current_user)
    dk_column = 5
    order_col = 0
    if _is_my_list:
        dk_column += 1
        order_col += 1
        if len(private_bottles):
            dk_column += 1
            order_col += 1

    heading_01 = (
        f"{user.username}'{'' if user.username.endswith('s') else 's'} Whiskies"
    )
    heading_02 = "Bottles"

    if type(entity) is Distillery:
        heading_01 += ": Distilleries"
        heading_02 = entity.name

    response = make_response(
        render_template(
            "bottle/bottle_list.html",
            title=f"{heading_01}: {heading_02}",
            heading_01=heading_01,
            heading_02=heading_02,
            has_datatable=True,
            user=user,
            bottles=bottles_to_list,
            has_killed_bottles=bool(len(killed_bottles)),
            bottle_types=BottleTypes,
            active_filters=active_bottle_types,
            dt_list_length=request.cookies.get("dt-list-length", "50"),
            show_privates=is_my_list and len(private_bottles),
            is_my_list=_is_my_list,
            dk_column=dk_column,
            order_col=order_col,
        )
    )

    return response
