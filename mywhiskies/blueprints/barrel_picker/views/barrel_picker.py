from flask import abort, flash, jsonify, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markupsafe import Markup

from mywhiskies.blueprints.barrel_picker import barrel_picker_bp
from mywhiskies.extensions import db
from mywhiskies.forms.barrel_picker import BarrelPickerAddForm, BarrelPickerEditForm
from mywhiskies.models import BarrelPicker, BottleTypes, User
from mywhiskies.services import utils
from mywhiskies.services.barrel_picker.barrel_picker import (
    add_barrel_picker,
    delete_barrel_picker,
    edit_barrel_picker,
    list_barrel_pickers,
)
from mywhiskies.services.bottle.bottle import list_bottles_for_entity

_VALID_SORTS = {"name", "bottles"}
_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100, 10000}


def _sorted_pickers():
    return sorted(current_user.barrel_pickers, key=lambda p: p.name)


@barrel_picker_bp.route("/<username>/barrel-pickers", methods=["GET"], endpoint="list")
def barrel_picker_list(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
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

    data = list_barrel_pickers(
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        page=page,
        per_page=per_page,
    )

    empty_text = "No barrel pickers match your search." if q else f"{user.username} has no barrel pickers. Yet."
    if data["total"] > 0:
        empty_text = ""

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    ctx = dict(
        title=f"{possessive} Whiskies: Barrel Pickers",
        heading_01=f"{possessive} Whiskies",
        heading_02="Barrel Pickers",
        user=user,
        is_my_list=_is_my_list,
        q=q,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("barrel_picker/_barrel_picker_rows.html", **ctx)

    return render_template("barrel_picker/list.html", **ctx)


@barrel_picker_bp.route(
    "/<username:username>/barrel_picker/<paddedint:user_num>",
    methods=["GET"],
    endpoint="detail",
)
def barrel_picker_detail(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    utils.check_privacy(user)
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=user.id, user_num=user_num))
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
        entity=picker,
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
    empty_text = ""
    if data["total"] == 0:
        empty_text = (
            "No bottles match your filters."
            if filters_active
            else f"{user.username} has no bottles picked by {picker.name}. Yet."
        )

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    list_url = url_for("barrel_picker.detail", username=user.username, user_num=picker.user_num)
    ctx = dict(
        title=f"{possessive} Whiskies: Barrel Pickers: {picker.name}",
        heading_01=f"{possessive} Whiskies: Barrel Pickers",
        heading_02=picker.name,
        user=user,
        picker=picker,
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

    return render_template("barrel_picker/detail.html", **ctx)


@barrel_picker_bp.route("/barrel-picker/add", methods=["GET", "POST"], endpoint="add")
@login_required
def barrel_picker_add_page():
    form = BarrelPickerAddForm()

    if form.validate_on_submit():
        duplicate = db.session.execute(
            db.select(BarrelPicker).filter_by(user_id=current_user.id, name=form.name.data.strip())
        ).scalar_one_or_none()
        if duplicate:
            form.name.errors.append("You already have a barrel picker with this name.")
        else:
            picker = add_barrel_picker(form, current_user)
            flash(Markup(f'Barrel picker "<strong>{picker.name}</strong>" has been added.'), "success")
            return redirect(url_for("barrel_picker.list", username=current_user.username))

    possessive = f"{current_user.username}'" if current_user.username.endswith("s") else f"{current_user.username}'s"
    return render_template(
        "barrel_picker/form.html",
        title=f"{possessive} Whiskies: Add Barrel Picker",
        picker=None,
        form=form,
    )


@barrel_picker_bp.route(
    "/<username:username>/barrel-picker/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def barrel_picker_edit(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=user.id, user_num=user_num))
    form = BarrelPickerEditForm(obj=picker if request.method != "POST" else None)

    if form.validate_on_submit():
        duplicate = db.session.execute(
            db.select(BarrelPicker).filter_by(user_id=current_user.id, name=form.name.data.strip())
        ).scalar_one_or_none()
        if duplicate and duplicate.id != picker.id:
            form.name.errors.append("You already have a barrel picker with this name.")
        else:
            edit_barrel_picker(form, picker)
            flash(Markup(f'Barrel picker "<strong>{picker.name}</strong>" has been updated.'), "success")
            return redirect(url_for("barrel_picker.list", username=current_user.username))

    possessive = f"{user.username}'" if user.username.endswith("s") else f"{user.username}'s"
    return render_template(
        "barrel_picker/form.html",
        title=f"{possessive} Whiskies: Edit Barrel Picker",
        picker=picker,
        form=form,
    )


@barrel_picker_bp.route(
    "/<username:username>/barrel-picker/<paddedint:user_num>/delete",
    endpoint="delete_page",
)
@login_required
def barrel_picker_delete_page(username: str, user_num: int):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    if user.id != current_user.id:
        abort(403)
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=user.id, user_num=user_num))
    ok, message = delete_barrel_picker(current_user, picker)
    flash(message, "success" if ok else "danger")
    return redirect(url_for("barrel_picker.list", username=current_user.username))


# --- Modal management endpoints ---


@barrel_picker_bp.route("/barrel_pickers/manage", endpoint="manage")
@login_required
def barrel_picker_manage():
    return render_template(
        "barrel_picker/_manage_body.html",
        barrel_pickers=_sorted_pickers(),
        add_form=BarrelPickerAddForm(formdata=None),
    )


@barrel_picker_bp.route("/barrel_pickers/options", endpoint="options")
@login_required
def barrel_picker_options():
    return jsonify([{"id": p.id, "name": p.name} for p in _sorted_pickers()])


@barrel_picker_bp.route("/barrel_picker/add", methods=["POST"], endpoint="modal_add")
@login_required
def barrel_picker_add():
    form = BarrelPickerAddForm()
    if form.validate_on_submit():
        duplicate = db.session.execute(
            db.select(BarrelPicker).filter_by(user_id=current_user.id, name=form.name.data.strip())
        ).scalar_one_or_none()
        if duplicate:
            form.name.errors.append("You already have a barrel picker with this name.")
        else:
            add_barrel_picker(form, current_user)
            form = BarrelPickerAddForm(formdata=None)
    return render_template(
        "barrel_picker/_manage_body.html",
        barrel_pickers=_sorted_pickers(),
        add_form=form,
    )


@barrel_picker_bp.route("/barrel_picker/<paddedint:user_num>/edit-form", endpoint="edit_form")
@login_required
def barrel_picker_edit_form(user_num: int):
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=current_user.id, user_num=user_num))
    return render_template(
        "barrel_picker/_edit_row.html",
        picker=picker,
        form=BarrelPickerEditForm(obj=picker),
    )


@barrel_picker_bp.route("/barrel_picker/<paddedint:user_num>/modal-edit", methods=["POST"], endpoint="modal_edit")
@login_required
def barrel_picker_modal_edit(user_num: int):
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=current_user.id, user_num=user_num))
    form = BarrelPickerEditForm()
    if form.validate_on_submit():
        duplicate = db.session.execute(
            db.select(BarrelPicker).filter_by(user_id=current_user.id, name=form.name.data.strip())
        ).scalar_one_or_none()
        if duplicate and duplicate.id != picker.id:
            form.name.errors.append("You already have a barrel picker with this name.")
        else:
            edit_barrel_picker(form, picker)
            return render_template("barrel_picker/_picker_list.html", barrel_pickers=_sorted_pickers())

    response = make_response(render_template("barrel_picker/_edit_row.html", picker=picker, form=form))
    response.headers["HX-Retarget"] = f"#picker-row-{picker.id}"
    response.headers["HX-Reswap"] = "outerHTML"
    return response


@barrel_picker_bp.route("/barrel_picker/<paddedint:user_num>/delete-confirm", endpoint="delete_confirm")
@login_required
def barrel_picker_delete_confirm(user_num: int):
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=current_user.id, user_num=user_num))
    return render_template("barrel_picker/_delete_confirm_row.html", picker=picker)


@barrel_picker_bp.route("/barrel_picker/<paddedint:user_num>/delete", endpoint="delete")
@login_required
def barrel_picker_delete(user_num: int):
    picker = db.one_or_404(db.select(BarrelPicker).filter_by(user_id=current_user.id, user_num=user_num))
    ok, message = delete_barrel_picker(current_user, picker)

    if request.headers.get("HX-Request"):
        return render_template("barrel_picker/_picker_list.html", barrel_pickers=_sorted_pickers())

    flash(message, "success" if ok else "danger")
    return redirect(url_for("bottle.list", username=current_user.username))
