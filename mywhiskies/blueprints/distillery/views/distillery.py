from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.extensions import db
from mywhiskies.forms.distillery import DistilleryAddForm, DistilleryEditForm
from mywhiskies.models import Distillery, User
from mywhiskies.services import utils
from mywhiskies.services.distillery.distillery import (
    add_distillery,
    bulk_add_distillery,
    delete_distillery,
    edit_distillery,
    get_distillery_detail,
    list_distilleries,
)

_VALID_SORTS = {"name", "bottles", "location"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100}


@distillery_bp.route("/no_distilleries")
@login_required
def no_distilleries():
    return render_template(
        "distillery/no_distilleries.html",
        title=f"{current_user.username}'s Whiskies: Add Distilleries",
        user=current_user,
    )


@distillery_bp.route("/bulk_distillery_add")
@login_required
def bulk_distillery_add():
    if len(current_user.distilleries) > 0:
        return redirect(url_for("core.main"))

    if not request.referrer:
        return redirect(url_for("core.main"))

    bulk_add_distillery(current_user, current_app)

    flash("New distilleries have been added to your account.")
    return redirect(url_for("core.main"))


@distillery_bp.route("/<username>/distilleries", methods=["GET"], endpoint="list")
def distilleries(username: str):
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

    data = list_distilleries(
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
    )

    empty_text = (
        "No distilleries match your search."
        if q
        else f"{user.username} has no distilleries. Yet."
    )
    if data["total"] > 0:
        empty_text = ""

    possessive = (
        f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    )
    ctx = dict(
        title=f"{possessive} Whiskies: Distilleries",
        heading_01=f"{possessive} Whiskies",
        heading_02="Distilleries",
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("distillery/_distillery_rows.html", **ctx)

    return render_template("distillery/list.html", **ctx)


@distillery_bp.route(
    "/<username:username>/distillery/<paddedint:user_num>",
    methods=["GET", "POST"],
    endpoint="detail",
)
def distillery_detail(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    distillery = db.one_or_404(
        db.select(Distillery).filter_by(user_id=user.id, user_num=user_num)
    )
    response = get_distillery_detail(distillery, request, current_user)
    utils.set_cookie_expiration(
        response, "dt-list-length", request.cookies.get("dt-list-length", "50")
    )
    return response


@distillery_bp.route("/distillery_add", methods=["GET", "POST"], endpoint="add")
@login_required
def distillery_add():
    form = DistilleryAddForm()

    if form.validate_on_submit():
        add_distillery(form, current_user)
        return redirect(url_for("distillery.list", username=current_user.username))

    return render_template(
        "distillery/add.html",
        title=f"{current_user.username}'s Whiskies: Add Distillery",
        user=current_user,
        form=form,
    )


@distillery_bp.route(
    "/<username:username>/distillery/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def distillery_edit(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    distillery = db.one_or_404(
        db.select(Distillery).filter_by(user_id=user.id, user_num=user_num)
    )
    form = DistilleryEditForm(obj=distillery if request.method != "POST" else None)

    if form.validate_on_submit():
        edit_distillery(form, distillery)
        return redirect(url_for("distillery.list", username=current_user.username))

    return render_template(
        "distillery/edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Distillery",
        distillery=distillery,
        form=form,
    )


@distillery_bp.route(
    "/<username:username>/distillery/<paddedint:user_num>/delete", endpoint="delete"
)
@login_required
def distillery_delete(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    distillery = db.one_or_404(
        db.select(Distillery).filter_by(user_id=user.id, user_num=user_num)
    )
    delete_distillery(current_user, distillery)
    return redirect(url_for("distillery.list", username=current_user.username))
