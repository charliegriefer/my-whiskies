import json
from uuid import UUID

from flask import abort, current_app, flash, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markupsafe import Markup

from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.extensions import db
from mywhiskies.forms.distillery import DistilleryAddForm, DistilleryEditForm, DistilleryQuickAddForm
from mywhiskies.models import BottleTypes, Distillery
from mywhiskies.services import utils
from mywhiskies.services.bottle.bottle import list_bottles_for_entity
from mywhiskies.services.distillery.distillery import (
    add_distillery,
    bulk_add_distillery,
    delete_distillery,
    edit_distillery,
    list_distilleries,
)

_VALID_SORTS = {"name", "bottles", "location"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100, 10000}


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
    is_htmx = bool(request.headers.get("HX-Request"))

    if len(current_user.distilleries) > 0:
        if is_htmx:
            return (
                '<div class="plan-notice plan-notice--success">'
                "<i class='bi bi-check-circle-fill'></i> You already have distilleries added."
                "</div>"
            )
        return redirect(url_for("core.main"))

    if not request.referrer and not is_htmx:
        return redirect(url_for("core.main"))

    bulk_add_distillery(current_user, current_app)

    if is_htmx:
        resp = make_response(
            '<div class="plan-notice plan-notice--success" id="distillery-nudge">'
            "<i class='bi bi-check-circle-fill'></i> "
            "Distilleries added! Pick one from the list below."
            "<button type='button' class='btn-close ms-auto' style='font-size:.7rem;' "
            "aria-label='Dismiss' onclick=\"document.getElementById('distillery-nudge').remove()\"></button>"
            "</div>"
        )
        resp.headers["HX-Trigger"] = "distilleryBulkAdded"
        return resp

    flash("New distilleries have been added to your account.")
    return redirect(url_for("core.main"))


@distillery_bp.route("/<username>/distilleries", methods=["GET"], endpoint="list")
def distilleries(username: str):
    user = utils.get_user_or_404(username)
    utils.check_privacy(user)
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

    data = list_distilleries(
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
    )

    empty_text = "No distilleries match your search." if q else f"{user.username} has no distilleries. Yet."
    if data["total"] > 0:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    ctx = dict(
        title=f"{possessive} Whiskies: Distilleries",
        heading_01=f"{possessive} Whiskies",
        heading_02="The Sources",
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
    "/<username:username>/distillery/<uuid:distillery_uuid>",
    endpoint="detail_legacy",
)
def distillery_legacy(username: str, distillery_uuid: UUID):
    _distillery = db.one_or_404(db.select(Distillery).filter_by(id=str(distillery_uuid)))
    return redirect(url_for("distillery.detail", username=username, user_num=_distillery.user_num), 301)


@distillery_bp.route(
    "/<username:username>/distillery/<paddedint:user_num>",
    methods=["GET"],
    endpoint="detail",
)
def distillery_detail(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    utils.check_privacy(user)
    _distillery = db.one_or_404(db.select(Distillery).filter_by(user_id=user.id, user_num=user_num))
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
        entity=_distillery,
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
        if not filters_active:
            empty_text = f"{user.username} has no bottles from {_distillery.name}. Yet."
        elif data["killed_matches"] > 0 and not show_killed:
            n = data["killed_matches"]
            bottle_word = "bottle" if n == 1 else "bottles"
            empty_text = Markup(
                f"No active bottles match your filters — "
                f"{n} killed {bottle_word} match. Toggle "
                f'<a href="#" onclick="var cb=document.getElementById(\'show_killed\');'
                f"if(cb){{cb.checked=true;htmx.trigger(cb,'change');}}return false;\">"
                f"Show Killed Bottles</a> to see them."
            )
        else:
            empty_text = "No bottles match your filters."
    else:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    list_url = url_for("distillery.detail", username=user.username, user_num=_distillery.user_num)
    ctx = dict(
        title=f"{possessive} Whiskies: Distilleries: {_distillery.name}",
        heading_01=f"{possessive} Whiskies: Distilleries",
        heading_02=_distillery.name,
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

    return render_template("distillery/detail.html", **ctx)


@distillery_bp.route("/distillery_add", methods=["GET", "POST"], endpoint="add")
@login_required
def distillery_add():
    form = DistilleryAddForm()

    if form.validate_on_submit():
        add_distillery(form, current_user)
        return redirect(url_for("distillery.list", username=current_user.username))

    return render_template(
        "distillery/form.html",
        title=f"{current_user.username}'s Whiskies: Add Distillery",
        user=current_user,
        distillery=None,
        form=form,
    )


@distillery_bp.route(
    "/<username:username>/distillery/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def distillery_edit(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    if user.id != current_user.id:
        abort(403)
    distillery = db.one_or_404(db.select(Distillery).filter_by(user_id=user.id, user_num=user_num))
    form = DistilleryEditForm(obj=distillery if request.method != "POST" else None)

    if form.validate_on_submit():
        edit_distillery(form, distillery)
        return redirect(url_for("distillery.list", username=current_user.username))

    return render_template(
        "distillery/form.html",
        title=f"{current_user.username}'s Whiskies: Edit Distillery",
        distillery=distillery,
        form=form,
    )


@distillery_bp.route("/distillery/quick-add", methods=["GET", "POST"], endpoint="quick_add")
@login_required
def distillery_quick_add():
    form = DistilleryQuickAddForm(formdata=request.form if request.method == "POST" else None)
    if form.validate_on_submit():
        duplicate = db.session.execute(
            db.select(Distillery).filter_by(user_id=current_user.id, name=form.name.data.strip())
        ).scalar_one_or_none()
        if duplicate:
            form.name.errors.append("You already have a distillery with this name.")
        else:
            distillery = Distillery(user_id=current_user.id)
            form.populate_obj(distillery)
            db.session.add(distillery)
            db.session.commit()
            response = make_response(render_template("distillery/_quick_add_success.html", name=distillery.name))
            trigger = {"closeModal": {"id": "quickAddDistilleryModal", "newId": str(distillery.id)}}
            response.headers["HX-Trigger"] = json.dumps(trigger)
            return response
    return render_template("distillery/_quick_add_form.html", form=form)


@distillery_bp.route("/distillery/options", endpoint="options")
@login_required
def distillery_options():
    distilleries = sorted(current_user.distilleries, key=lambda d: d.name.lower())
    return jsonify([{"id": d.id, "name": d.name} for d in distilleries])


@distillery_bp.route("/distillery/<uuid:distillery_id>/rename", methods=["POST"], endpoint="rename")
@login_required
def distillery_rename(distillery_id):
    distillery = db.one_or_404(db.select(Distillery).filter_by(id=distillery_id))
    if distillery.user_id != current_user.id:
        abort(403)
    name = (request.json or {}).get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    distillery.name = name
    db.session.commit()
    return jsonify({"name": distillery.name})


@distillery_bp.route("/<username:username>/distillery/<paddedint:user_num>/delete", endpoint="delete")
@login_required
def distillery_delete(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    if user.id != current_user.id:
        abort(403)
    distillery = db.one_or_404(db.select(Distillery).filter_by(user_id=user.id, user_num=user_num))
    delete_distillery(current_user, distillery)
    return redirect(url_for("distillery.list", username=current_user.username))
