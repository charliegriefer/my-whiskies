import random
from datetime import datetime
from typing import List, Tuple, Union

from dateutil.relativedelta import relativedelta
from flask import abort, flash, make_response, render_template, request
from flask.wrappers import Response
from flask_wtf import FlaskForm as Form
from markupsafe import Markup

from mywhiskies.models import Bottle, Bottler, BottleTypes, Distillery, User


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


def set_cookie_expiration(
    response: Response, cookie_name: str, value: str, years: int = 1
) -> None:
    response.set_cookie(
        cookie_name,
        value=value,
        expires=datetime.now() + relativedelta(years=years),
    )


def prep_datatable_bottles(
    entity: Union[Bottler, Distillery, User], current_user: User, request: request
) -> Response:
    # The same template is used for distilleries, bottlers, and users. Prep the request accordingly.
    if type(entity) in [Distillery, Bottler]:
        user = entity.user
    else:
        user = entity

    _is_my_list = is_my_list(user.username, current_user)

    # set the bottle filter types. If none are selected (on a GET, for example), default to all types.
    active_bottle_types = request.form.getlist("filter_bottle_type") or [
        b.name for b in BottleTypes
    ]
    bottles = [b for b in entity.bottles if b.type.name in active_bottle_types]

    if not _is_my_list:
        bottles = [b for b in bottles if not b.is_private]

    show_filters = True
    show_random_btn = _is_my_list
    show_all_btn = False
    show_killed_toggle = any(b.date_killed for b in bottles)

    if request.form.get("random_toggle", 0, type=int):
        bottles = _get_random_bottle(bottles)
        show_filters = False
        show_random_btn = False
        show_all_btn = True
        show_killed_toggle = False

    has_privates = any(b.is_private for b in bottles)
    date_killed_column, order_column = _set_columns(_is_my_list, has_privates)
    heading_01, heading_02 = _set_headings(user.username, entity)

    response = make_response(
        render_template(
            "shared/datatable/bottles/list.html",
            location="bottles",
            title=f"{heading_01}: {heading_02}",
            heading_01=heading_01,
            heading_02=heading_02,
            has_datatable=True,
            user=user,
            bottles=bottles,
            bottle_types=BottleTypes,
            active_bottle_types=active_bottle_types,
            dt_list_length=request.cookies.get("dt-list-length", "50"),
            is_my_list=_is_my_list,
            show_privates=_is_my_list and has_privates,
            date_killed_column=date_killed_column,
            order_column=order_column,
            empty_text=_set_empty_text(entity, user, active_bottle_types),
            entity=entity,
            show_killed_toggle=show_killed_toggle,
            show_filters=show_filters and len(bottles),
            show_random_btn=show_random_btn,
            show_all_btn=show_all_btn,
        )
    )

    return response


def prep_datatable_entities(
    user: User, current_user: User, request: request, entity_type: str
) -> Response:
    if entity_type not in ["bottlers", "distilleries"]:
        abort(404)

    entities = getattr(user, entity_type, None)
    if entities is None:
        abort(404)

    response = make_response(
        render_template(
            "shared/datatable/non_bottles/list.html",
            location="non_bottles",
            title=f"{user.username}'s Whiskies: {entity_type.title()}",
            heading_01=f"{user.username}'s Whiskies",
            heading_02=entity_type.title(),
            has_datatable=True,
            user=user,
            entities=entities,
            dt_list_length=request.cookies.get("dt-list-length", "50"),
            is_my_list=is_my_list(user.username, current_user),
            entity_type=entity_type,
        )
    )
    return response


def _set_columns(_is_my_list: bool, has_privates: bool) -> Tuple[int, int]:
    # Convenience method to determine the index of the date_killed column and the initial ordered column.
    date_killed_column = 5
    order_column = 0
    if _is_my_list:
        date_killed_column += 1
        order_column += 1
        if has_privates:
            date_killed_column += 1
            order_column += 1
    return date_killed_column, order_column


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


def _set_empty_text(
    entity: Union[Bottler, Distillery, User], user: User, active_bottle_types: List[str]
) -> str:
    # Convenience method to set the empty table text for the datatable.
    if type(entity) in [Distillery, Bottler]:
        empty_text = f"{entity.user.username} has no bottles from {entity.name}. Yet."
    elif type(entity) is User:
        empty_text = f"{entity.username} has no bottles. Yet."
    else:
        return "No bottles found."

    if len(active_bottle_types) < len(BottleTypes):
        if len(active_bottle_types) == 1:
            empty_text = f"{user.username} has no {BottleTypes[active_bottle_types[0]].value} bottles. Yet."
        else:
            empty_text = f"{user.username} has no bottles of the selected types. Yet."

    return empty_text


def _get_random_bottle(bottles: List[Bottle]) -> List[Bottle]:
    """
    Selects a random bottle from the provided list.
    Only non-killed bottles are considered.

    Returns an empty list if no active bottles exist.
    """
    active_bottles = [b for b in bottles if not b.date_killed]
    return [random.choice(active_bottles)] if active_bottles else []
