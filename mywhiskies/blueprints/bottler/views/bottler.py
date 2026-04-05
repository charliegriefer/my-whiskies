from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.extensions import db
from mywhiskies.forms.bottler import BottlerAddForm, BottlerEditForm
from mywhiskies.models import Bottle, BottleTypes, Bottler, User
from mywhiskies.services import utils
from mywhiskies.services.bottle.bottle import list_bottles_for_entity
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    list_bottlers,
)

_VALID_SORTS = {"name", "bottles", "location"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100, 10000}


@bottler_bp.route("/<username:username>/bottlers", methods=["GET"], endpoint="list")
def bottlers(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _is_my_list = utils.is_my_list(username, current_user)

    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "name")
    if sort not in _VALID_SORTS:
        sort = "name"
    direction = request.args.get("dir", "asc")
    if direction not in _VALID_DIRS:
        direction = "asc"
    page = max(1, request.args.get("page", 1, type=int))
    per_page = request.args.get("per_page", type=int)
    if per_page not in _VALID_PER_PAGE:
        per_page = int(request.cookies.get("per_page", 25))
    if per_page not in _VALID_PER_PAGE:
        per_page = 25

    data = list_bottlers(
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
    )

    empty_text = "No bottlers match your search." if q else f"{user.username} has no bottlers. Yet."
    if data["total"] > 0:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    ctx = dict(
        title=f"{possessive} Whiskies: Bottlers",
        heading_01=f"{possessive} Whiskies",
        heading_02="Bottlers",
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("bottler/_bottler_rows.html", **ctx)

    return render_template("bottler/list.html", **ctx)


@bottler_bp.route(
    "/<username:username>/bottler/<paddedint:user_num>",
    methods=["GET"],
    endpoint="detail",
)
def bottler(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _bottler = db.one_or_404(db.select(Bottler).filter_by(user_id=user.id, user_num=user_num))
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
    per_page = request.args.get("per_page", type=int)
    if per_page not in _VALID_PER_PAGE:
        per_page = int(request.cookies.get("per_page", 25))
    if per_page not in _VALID_PER_PAGE:
        per_page = 25

    data = list_bottles_for_entity(
        entity=_bottler,
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
        empty_text = (
            "No bottles match your filters."
            if filters_active
            else f"{user.username} has no bottles from {_bottler.name}. Yet."
        )
    else:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    list_url = url_for("bottler.detail", username=user.username, user_num=_bottler.user_num)
    ctx = dict(
        title=f"{possessive} Whiskies: Bottlers: {_bottler.name}",
        heading_01=f"{possessive} Whiskies: Bottlers",
        heading_02=_bottler.name,
        user=user,
        is_my_list=_is_my_list,
        bottle_types=BottleTypes,
        q=q,
        types=types,
        show_killed=show_killed,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        list_url=list_url,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("bottle/_bottle_rows.html", **ctx)

    return render_template("bottler/detail.html", **ctx)


@bottler_bp.route("/bottler/add", methods=["GET", "POST"], endpoint="add")
@login_required
def bottler_add():
    form = BottlerAddForm()

    if form.validate_on_submit():
        add_bottler(form, current_user)
        return redirect(url_for("core.main"))

    return render_template(
        "bottler/add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottler",
        user=current_user,
        form=form,
    )


@bottler_bp.route(
    "/<username:username>/bottler/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def bottler_edit(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    _bottler = db.one_or_404(db.select(Bottler).filter_by(user_id=user.id, user_num=user_num))
    form = BottlerEditForm(obj=_bottler)

    if form.validate_on_submit():
        edit_bottler(form, _bottler)
        return redirect(url_for("bottler.list", username=current_user.username))

    return render_template(
        "bottler/edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottler",
        bottler=_bottler,
        form=form,
    )


@bottler_bp.route(
    "/<username:username>/bottler/<paddedint:user_num>/delete", endpoint="delete"
)
@login_required
def bottler_delete(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _bottler = db.one_or_404(db.select(Bottler).filter_by(user_id=user.id, user_num=user_num))
    delete_bottler(current_user, _bottler)
    return redirect(url_for("bottler.list", username=current_user.username))
