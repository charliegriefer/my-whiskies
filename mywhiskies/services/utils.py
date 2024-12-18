import random
from datetime import datetime
from typing import Tuple, Union

from dateutil.relativedelta import relativedelta
from flask import Markup, flash, make_response, render_template, request
from flask.wrappers import Response

from mywhiskies.blueprints.bottle.models import BottleTypes
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User


def is_my_list(username, current_user) -> bool:
    # is the current user logged in and viewing their own bottles?
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


def prep_dt2(user, current_user, request):
    response = make_response(
        render_template(
            "shared/datatable/entities/list.html",
            title=f"{user.username}'s Whiskies: Bottlers",
            has_datatable=True,
            is_my_list=is_my_list(user.username, current_user),
            user=user,
            dt_list_length=50,
        )
    )
    return response


def prep_datatables(
    entity: Union[Bottler, Distillery, User], current_user: User, request: request
) -> Response:
    # The same template is used for distilleries, bottlers, and users. Prep the request accordingly.
    if type(entity) in [Distillery, Bottler]:
        user = entity.user
    else:
        user = entity

    all_bottles = entity.bottles
    killed_bottles = [b for b in all_bottles if b.date_killed]
    private_bottles = [b for b in all_bottles if b.is_private]

    _is_my_list = is_my_list(user.username, current_user)

    if request.method == "POST":
        # user has either filtered on a bottle type or requested a random bottle
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
        if _is_my_list:
            bottles_to_list = all_bottles
        else:
            bottles_to_list = [
                bottle for bottle in all_bottles if not bottle.is_private
            ]

    dk_column, order_col = _set_columns(_is_my_list, len(private_bottles))
    heading_01, heading_02 = _set_headings(user.username, entity)

    response = make_response(
        render_template(
            "shared/datatable/bottles/list.html",
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
            show_privates=_is_my_list and len(private_bottles),
            is_my_list=_is_my_list,
            dk_column=dk_column,
            order_col=order_col,
        )
    )

    return response


def _set_columns(_is_my_list: bool, private_bottles: int) -> Tuple[int, int]:
    # Convenience method to determine the index of the date_killed column and the initial ordered column.
    dk_column = 5
    order_col = 0
    if _is_my_list:
        dk_column += 1
        order_col += 1
        if private_bottles:
            dk_column += 1
            order_col += 1
    return dk_column, order_col


def _set_headings(
    username: str, entity: Union[Bottler, Distillery, User]
) -> Tuple[str, str]:
    # Convenience method to set the appropriate headings for the datatable.
    heading_01 = f"{username}'{'' if username.endswith('s') else 's'} Whiskies"
    heading_02 = "Bottles"

    if type(entity) is Distillery:
        heading_01 += ": Distilleries"
        heading_02 = entity.name
    elif type(entity) is Bottler:
        heading_01 += ": Bottlers"
        heading_02 = entity.name

    return heading_01, heading_02
