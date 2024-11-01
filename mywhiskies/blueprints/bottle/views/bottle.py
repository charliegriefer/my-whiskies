import time
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.blueprints.bottle.forms import BottleEditForm, BottleForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    list_bottles,
)
from mywhiskies.services.bottle.form import prepare_bottle_form
from mywhiskies.services.bottle.image import get_s3_config


@bottle_bp.route(
    "/<username>/bottles",
    methods=["GET", "POST"],
    endpoint="list_bottles",
    strict_slashes=False,
)
def bottles(username: str):
    dt_list_length = request.cookies.get("dt-list-length", "50")
    user = db.one_or_404(db.select(User).filter_by(username=username))

    bottles_to_list, active_bottle_types, is_my_list, killed_bottles = list_bottles(
        user, request
    )

    response = make_response(
        render_template(
            "bottle/bottle_list.html",
            title=f"{user.username}'s Whiskies: Bottles",
            has_datatable=True,
            user=user,
            bottles=bottles_to_list,
            has_killed_bottles=bool(len(killed_bottles)),
            bottle_types=BottleTypes,
            active_filters=active_bottle_types,
            dt_list_length=dt_list_length,
            is_my_list=is_my_list,
        )
    )

    response.set_cookie(
        "dt-list-length",
        value=dt_list_length,
        expires=datetime.now() + relativedelta(years=1),
    )
    return response


@bottle_bp.route("/bottle/<bottle_id>")
def bottle_detail(bottle_id: str):
    _bottle = db.get_or_404(Bottle, bottle_id)
    _, _, img_s3_url = get_s3_config()
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    return render_template(
        "bottle/bottle_detail.html",
        title=f"{_bottle.user.username}'s Whiskies: {_bottle.name}",
        bottle=_bottle,
        user=_bottle.user,
        img_s3_url=img_s3_url,
        ts=time.time(),
        is_my_bottle=is_my_bottle,
    )


@bottle_bp.route("/bottle/add", methods=["GET", "POST"])
@login_required
def bottle_add():
    form = prepare_bottle_form(current_user, BottleForm())

    if form.validate_on_submit():
        add_bottle(form, current_user)
        return redirect(url_for("core.home", username=current_user.username.lower()))

    return render_template(
        "bottle/bottle_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottle",
        form=form,
    )


@bottle_bp.route("/bottle/edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    _, _, img_s3_url = get_s3_config()
    _bottle = db.get_or_404(Bottle, bottle_id)
    form = prepare_bottle_form(current_user, BottleEditForm(obj=_bottle))
    form.type.data = _bottle.type.name
    form.distilleries.data = [d.id for d in _bottle.distilleries]

    if form.validate_on_submit():
        edit_bottle(form, _bottle)
        return redirect(url_for("core.home", username=current_user.username.lower()))

    return render_template(
        "bottle/bottle_edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottle",
        bottle=_bottle,
        form=form,
        img_s3_url=img_s3_url,
    )


@bottle_bp.route("/bottle/delete/<string:bottle_id>")
@login_required
def bottle_delete(bottle_id: str):
    delete_bottle(bottle_id)
    return redirect(
        url_for("bottle.list_bottles", username=current_user.username.lower())
    )
