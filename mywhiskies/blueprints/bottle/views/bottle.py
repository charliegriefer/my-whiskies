import time

from flask import abort, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.extensions import db
from mywhiskies.forms.bottle import BottleAddForm, BottleEditForm
from mywhiskies.models import Bottle, BottleTypes, User
from mywhiskies.services import utils
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    get_random_bottle,
    list_bottles_by_user,
)
from mywhiskies.services.bottle.form import prep_bottle_form
from mywhiskies.services.bottle.image import get_s3_config

_VALID_SORTS = {"name", "type", "abv", "rating", "sb", "private"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100}


@bottle_bp.route("/<username:username>/bottles", methods=["GET"], endpoint="list")
def bottles(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _is_my_list = utils.is_my_list(username, current_user)

    all_type_names = [b.name for b in BottleTypes]
    q = request.args.get("q", "").strip()
    types = request.args.getlist("types") or all_type_names
    show_killed = request.args.get("killed") == "1"
    sort = request.args.get("sort", "name")
    if sort not in _VALID_SORTS:
        sort = "name"
    direction = request.args.get("dir", "asc")
    if direction not in _VALID_DIRS:
        direction = "asc"
    page = max(1, request.args.get("page", 1, type=int))
    per_page = request.args.get("per_page", 25, type=int)
    if per_page not in _VALID_PER_PAGE:
        per_page = 25

    data = list_bottles_by_user(
        user=user,
        is_my_list=_is_my_list,
        q=q,
        types=types,
        show_killed=show_killed,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
    )

    filters_active = bool(q) or set(types) != set(all_type_names)
    if data["total"] == 0:
        empty_text = "No bottles match your filters." if filters_active else f"{user.username} has no bottles. Yet."
    else:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    ctx = dict(
        title=f"{possessive} Whiskies: Bottles",
        heading_01=f"{possessive} Whiskies",
        heading_02="Bottles",
        user=user,
        is_my_list=_is_my_list,
        bottle_types=BottleTypes,
        q=q,
        types=types,
        show_killed=show_killed,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("bottle/_bottle_rows.html", **ctx)

    return render_template("bottle/list.html", **ctx)


@bottle_bp.route("/<username:username>/bottle/random", endpoint="random")
@login_required
def bottle_random(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    bottle = get_random_bottle(user)
    if bottle:
        return redirect(url_for("bottle.detail", username=username, user_num=bottle.user_num))
    return redirect(url_for("bottle.list", username=username))


@bottle_bp.route("/<username:username>/bottle/<paddedint:user_num>", endpoint="detail")
def bottle(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    _, _, img_s3_url = get_s3_config()
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    if not is_my_bottle:
        _bottle.personal_note = None
        if _bottle.is_private:
            abort(404)

    g.bottle_og_image_url = (
        f"{img_s3_url}/{_bottle.id}_1.jpg"
        if _bottle.images
        else url_for("static", filename="logo.png", _external=True)
    )

    return render_template(
        "bottle/bottle.html",
        title=f"{_bottle.user.username}'s Whiskies: {_bottle.name}",
        bottle=_bottle,
        user=_bottle.user,
        img_s3_url=img_s3_url,
        ts=time.time(),
        is_my_bottle=is_my_bottle,
    )


@bottle_bp.route("/bottle/add", methods=["GET", "POST"], endpoint="add")
@login_required
def bottle_add():
    if not current_user.distilleries:
        return redirect(url_for("distillery.no_distilleries"))

    form = prep_bottle_form(current_user, BottleAddForm())

    if form.validate_on_submit():
        bottle = add_bottle(form, current_user)
        if bottle:
            return redirect(url_for("bottle.list", username=current_user.username))

    return render_template(
        "bottle/add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottle",
        form=form,
    )


@bottle_bp.route(
    "/<username:username>/bottle/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def bottle_edit(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    _, _, img_s3_url = get_s3_config()

    images = [None] * 3
    for img in _bottle.images:
        images[img.sequence - 1] = img

    form = prep_bottle_form(current_user, BottleEditForm(obj=_bottle))
    if form.validate_on_submit():
        edit_bottle(form, _bottle)
        return redirect(url_for("bottle.detail", username=username, user_num=user_num))
    else:
        form.type.data = _bottle.type.name
        form.distilleries.data = [d.id for d in _bottle.distilleries]

    return render_template(
        "bottle/edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottle",
        bottle=_bottle,
        form=form,
        img_s3_url=img_s3_url,
        images=images,
    )


@bottle_bp.route(
    "/<username:username>/bottle/<paddedint:user_num>/delete", endpoint="delete"
)
@login_required
def bottle_delete(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    delete_bottle(current_user, _bottle)
    return redirect(url_for("bottle.list", username=current_user.username))
