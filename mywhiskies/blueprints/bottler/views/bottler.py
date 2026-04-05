from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.extensions import db
from mywhiskies.forms.bottler import BottlerAddForm, BottlerEditForm
from mywhiskies.models import Bottler, User
from mywhiskies.services import utils
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    get_bottler_detail,
    list_bottlers,
)

_VALID_SORTS = {"name", "bottles", "location"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100}


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
    per_page = request.args.get("per_page", 25, type=int)
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
    methods=["GET", "POST"],
    endpoint="detail",
)
def bottler(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    _bottler = db.one_or_404(db.select(Bottler).filter_by(user_id=user.id, user_num=user_num))
    response = get_bottler_detail(_bottler, request, current_user)
    utils.set_cookie_expiration(
        response, "dt-list-length", request.cookies.get("dt-list-length", "50")
    )
    return response


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
