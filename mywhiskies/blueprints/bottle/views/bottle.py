import time
from urllib.parse import urlparse
from uuid import UUID

from flask import abort, current_app, flash, g, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markupsafe import Markup

from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.extensions import db
from mywhiskies.forms.bottle import BottleAddForm, BottleEditForm
from mywhiskies.models import Bottle, BottleTypes
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
from mywhiskies.services.bottle.scan import scan_bottle_label

_VALID_SORTS = {"name", "type", "abv", "rating", "sb", "private"}


def _is_safe_url(url: str) -> bool:
    """Return True if the URL is local (safe to redirect to)."""
    parsed = urlparse(url)
    return not parsed.netloc or parsed.netloc == urlparse(request.host_url).netloc


_VALID_DIRS = {"asc", "desc"}
_VALID_PER_PAGE = {25, 50, 100, 10000}


@bottle_bp.route("/<username:username>/bottles", methods=["GET"], endpoint="list")
def bottles(username: str):
    user = utils.get_user_or_404(username)
    utils.check_privacy(user)
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

    _, _, img_s3_url = get_s3_config()

    filters_active = bool(q) or set(types) != set(all_type_names)
    if data["total"] == 0:
        if not filters_active:
            empty_text = f"{user.username} has no bottles. Yet."
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
    ctx = dict(
        title=f"{possessive} Whiskies: Bottles",
        heading_01=f"{possessive} Whiskies",
        heading_02="The Collection",
        user=user,
        is_my_list=_is_my_list,
        bottle_types=BottleTypes,
        q=q,
        types=types,
        show_killed=show_killed,
        sort=sort,
        direction=direction,
        empty_text=empty_text,
        list_url=url_for("bottle.list", username=user.username),
        img_s3_url=img_s3_url,
        **data,
    )

    if request.headers.get("HX-Request"):
        return render_template("bottle/_bottle_rows.html", **ctx)

    return render_template("bottle/list.html", **ctx)


@bottle_bp.route("/<username:username>/bottle/random", endpoint="random")
@login_required
def bottle_random(username: str):
    user = utils.get_user_or_404(username)
    if user.id != current_user.id:
        abort(403)
    q = request.args.get("q", "").strip()
    all_type_names = [b.name for b in BottleTypes]
    types = request.args.getlist("types") or all_type_names
    bottle = get_random_bottle(user, q=q, types=types)
    if bottle:
        return redirect(url_for("bottle.detail", username=username, user_num=bottle.user_num))
    return redirect(url_for("bottle.list", username=username))


@bottle_bp.route("/<username:username>/bottle/<uuid:bottle_uuid>", endpoint="detail_legacy")
def bottle_legacy(username: str, bottle_uuid: UUID):
    _bottle = db.one_or_404(db.select(Bottle).filter_by(id=str(bottle_uuid)))
    return redirect(url_for("bottle.detail", username=username, user_num=_bottle.user_num), 301)


@bottle_bp.route("/<username:username>/bottle/<paddedint:user_num>", endpoint="detail")
def bottle(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    utils.check_privacy(user)
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    _, _, img_s3_url = get_s3_config()
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    if not is_my_bottle:
        _bottle.personal_note = None
        if _bottle.is_private:
            abort(404)

    g.bottle_og_image_url = (
        f"{img_s3_url}/{_bottle.id}_1.jpg" if _bottle.images else url_for("static", filename="glen.png", _external=True)
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

    limit = current_app.config["FREE_TIER_BOTTLE_LIMIT"]
    if not current_user.is_pro and len(current_user.bottles) >= limit:
        flash(
            f"You've reached the {limit}-bottle limit for free accounts. Upgrade to Pro for unlimited bottles.",
            "warning",
        )
        return redirect(url_for("payments.upgrade"))

    form = prep_bottle_form(current_user, BottleAddForm())
    _, _, img_s3_url = get_s3_config()

    if form.validate_on_submit():
        bottle = add_bottle(form, current_user)
        if bottle:
            return redirect(url_for("bottle.list", username=current_user.username))

    return render_template(
        "bottle/form.html",
        title=f"{current_user.username}'s Whiskies: Add Bottle",
        bottle=None,
        form=form,
        img_s3_url=img_s3_url,
        existing_images=[],
        next_url="",
    )


@bottle_bp.route(
    "/<username:username>/bottle/<paddedint:user_num>/edit",
    methods=["GET", "POST"],
    endpoint="edit",
)
@login_required
def bottle_edit(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    if user.id != current_user.id:
        abort(403)
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    _, _, img_s3_url = get_s3_config()

    next_url = request.args.get("next") or request.form.get("next") or ""
    if next_url and not _is_safe_url(next_url):
        next_url = ""

    form = prep_bottle_form(current_user, BottleEditForm(obj=_bottle))
    if form.validate_on_submit():
        edit_bottle(form, _bottle)
        return redirect(next_url or url_for("bottle.detail", username=username, user_num=user_num))
    else:
        form.type.data = _bottle.type.name
        form.distilleries.data = [d.id for d in _bottle.distilleries]
        form.barrel_pickers.data = [p.id for p in _bottle.barrel_pickers]

    return render_template(
        "bottle/form.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottle",
        bottle=_bottle,
        form=form,
        img_s3_url=img_s3_url,
        existing_images=list(_bottle.images),
        next_url=next_url,
    )


@bottle_bp.route("/bottle/scan-label", methods=["POST"], endpoint="scan_label")
@login_required
def bottle_scan_label():
    if not current_user.is_pro:
        if current_user.glen_scan_count >= current_app.config["FREE_TIER_SCAN_LIMIT"]:
            return jsonify({"error": "scan_limit_reached"}), 403
    files = request.files.getlist("image")
    if not files:
        return jsonify({"error": "No image provided"}), 400
    images = [(f.read(), f.mimetype or "image/jpeg") for f in files]
    result = scan_bottle_label(images)
    if result is None:
        return jsonify({"error": "Scan failed"}), 502
    if not current_user.is_pro:
        current_user.glen_scan_count += 1
        db.session.commit()
    return jsonify(result)


@bottle_bp.route("/<username:username>/bottle/<paddedint:user_num>/delete", endpoint="delete")
@login_required
def bottle_delete(username: str, user_num: int):
    user = utils.get_user_or_404(username)
    if user.id != current_user.id:
        abort(403)
    _bottle = db.one_or_404(db.select(Bottle).filter_by(user_id=user.id, user_num=user_num))
    delete_bottle(current_user, _bottle)
    next_url = request.args.get("next", "")
    if next_url and not _is_safe_url(next_url):
        next_url = ""
    return redirect(next_url or url_for("bottle.list", username=current_user.username))
