import time

from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    list_bottles_by_user,
)
from mywhiskies.services.bottle.form import prep_bottle_form
from mywhiskies.services.bottle.image import get_s3_config


@bottle_bp.route("/<string:username>/bottles", methods=["GET", "POST"])
def bottles(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_bottles_by_user(user, request, current_user)
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("dt-list-length", "50")
    )
    return response


@bottle_bp.route("/<string:username>/bottle/<bottle_id>")
def bottle(username: str, bottle_id: str):
    _bottle = db.get_or_404(Bottle, bottle_id)
    _, _, img_s3_url = get_s3_config()
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    if not is_my_bottle:
        _bottle.personal_note = None
        if _bottle.is_private:
            abort(404)

    return render_template(
        "bottle/bottle.html",
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
    if not current_user.distilleries:
        return redirect(
            url_for("distillery.no_distilleries", username=current_user.username)
        )
    form = prep_bottle_form(current_user, BottleAddForm())
    if form.validate_on_submit():
        add_bottle(form, current_user)
        return redirect(url_for("bottle.bottles", username=current_user.username))
    return render_template(
        "bottle/bottle_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottle",
        form=form,
    )


@bottle_bp.route("/bottle/edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    _bottle = db.get_or_404(Bottle, bottle_id)
    _, _, img_s3_url = get_s3_config()
    form = prep_bottle_form(current_user, BottleEditForm(obj=_bottle))
    if form.validate_on_submit():
        edit_bottle(form, _bottle)
        return redirect(
            url_for(
                "bottle.bottle",
                bottle_id=bottle_id,
                username=current_user.username,
            )
        )
    else:
        form.type.data = _bottle.type.name
        form.distilleries.data = [d.id for d in _bottle.distilleries]

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
    delete_bottle(current_user, bottle_id)
    return redirect(url_for("bottle.bottles", username=current_user.username))
