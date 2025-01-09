import json
import os

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import insert

from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.blueprints.distillery.forms import DistilleryEditForm, DistilleryForm
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils
from mywhiskies.services.distillery.distillery import (
    add_distillery,
    delete_distillery,
    edit_distillery,
    get_distillery_detail,
    list_distilleries,
)


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
    """
    Bulk add distilleries.
    ---
    get:
        summary: For users with no distilleries listed yet, bulk adds distilleries.
        description: JSON file in static holds the base distilleries to add.
                     This page will redirect user home if the user already has distilleries.
                     Likewise, will redirect the user home if they access the page directly (no referrer).
        parameters:
            - na/
        responses:
            200:
                description: Distilleries are added, user is redirected to home page.
    """
    if len(current_user.distilleries) > 0:
        return redirect(url_for("core.main"))

    if not request.referrer:
        return redirect(url_for("core.main"))

    json_file = os.path.join(
        current_app.static_folder, "data", "base_distilleries.json"
    )
    with open(json_file, mode="r", encoding="utf-8") as f:
        data = json.load(f)

        base_distilleries = data.get("distilleries")
        for distillery in base_distilleries:
            distillery["user_id"] = current_user.id

        db.session.execute(insert(Distillery), base_distilleries)
        db.session.commit()

    flash(f"{len(base_distilleries)} distilleries have been added to your account.")
    return redirect(url_for("core.main", username=current_user.username))


@distillery_bp.route("/<username>/distilleries", endpoint="distillery_list")
def distilleries(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_distilleries(user, current_user, request, "distilleries")
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("bt-list-length", "50")
    )
    return response


@distillery_bp.route("/distillery/<string:distillery_id>", methods=["GET", "POST"])
def distillery_detail(distillery_id: str):
    distillery = db.one_or_404(db.select(Distillery).filter_by(id=distillery_id))
    response = get_distillery_detail(distillery, request, current_user)
    utils.set_cookie_expiration(
        response, "dt-list-length", request.cookies.get("dt-list-length", "50")
    )
    return response


@distillery_bp.route("/distillery_add", methods=["GET", "POST"])
@login_required
def distillery_add():
    form = DistilleryForm()

    if form.validate_on_submit():
        add_distillery(form, current_user)
        return redirect(
            url_for("distillery.distillery_list", username=current_user.username)
        )

    return render_template(
        "distillery/distillery_add.html",
        title=f"{current_user.username}'s Whiskies: Add Distillery",
        user=current_user,
        form=form,
    )


@distillery_bp.route("/distillery_edit/<string:distillery_id>", methods=["GET", "POST"])
@login_required
def distillery_edit(distillery_id: str):
    distillery = db.get_or_404(Distillery, distillery_id)
    form = DistilleryEditForm(obj=distillery if request.method != "POST" else None)

    if form.validate_on_submit():
        edit_distillery(form, distillery)
        return redirect(
            url_for("distillery.distillery_list", username=current_user.username)
        )

    return render_template(
        "distillery/distillery_edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Distillery",
        distillery=distillery,
        form=form,
    )


@distillery_bp.route("/distillery_delete/<string:distillery_id>")
@login_required
def distillery_delete(distillery_id: str):
    delete_distillery(distillery_id, current_user)
    return redirect(
        url_for("distillery.distillery_list", username=current_user.username)
    )
