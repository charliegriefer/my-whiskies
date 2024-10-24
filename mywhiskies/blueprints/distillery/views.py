import json
import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import insert, select
from sqlalchemy.sql.expression import func

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.distillery.forms import DistilleryEditForm, DistilleryForm
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

distillery = Blueprint("distillery", __name__, template_folder="templates")


@distillery.route("/bulk_distillery_add")
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
        return redirect(url_for("core.home", username=current_user.username.lower()))

    if not request.referrer:
        return redirect(url_for("core.home", username=current_user.username.lower()))

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
    return redirect(url_for("core.home", username=current_user.username.lower()))


@distillery.route(
    "/<username>/distilleries", endpoint="distilleries_list", strict_slashes=False
)
def distilleries_list(username: str):
    """Don't need a big docstring here. This endpoint lists a user's distilleries."""
    dt_list_length = request.cookies.get("dt-list-length", "50")
    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )
    user = db.one_or_404(db.select(User).filter_by(username=username))

    response = make_response(
        render_template(
            "distillery/distillery_list.html",
            title=f"{user.username}'s Whiskies: Distilleries",
            has_datatable=True,
            is_my_list=is_my_list,
            user=user,
            dt_list_length=dt_list_length,
        )
    )
    response.set_cookie(
        "dt-list-length",
        value=dt_list_length,
        expires=datetime.now() + relativedelta(years=1),
    )
    return response


@distillery.route("/distillery_add", methods=["GET", "POST"])
@login_required
def distillery_add():
    form = DistilleryForm()

    if request.method == "POST" and form.validate_on_submit():
        distillery_in = Distillery(user_id=current_user.id)
        form.populate_obj(distillery_in)
        db.session.add(distillery_in)
        db.session.commit()
        flash(f'"{distillery_in.name}" has been successfully added.', "success")
        return redirect(url_for("core.home", username=current_user.username.lower()))
    return render_template(
        "distillery/distillery_add.html",
        title=f"{current_user.username}'s Whiskies: Add Distillery",
        user=current_user,
        form=form,
    )


@distillery.route("/distillery_edit/<string:distillery_id>", methods=["GET", "POST"])
@login_required
def distillery_edit(distillery_id: str):
    _distillery = db.get_or_404(Distillery, distillery_id)
    form = DistilleryEditForm(obj=_distillery)
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_distillery)

        db.session.add(_distillery)
        db.session.commit()
        flash(f'"{_distillery.name}" has been successfully updated.', "success")
        return redirect(
            url_for(
                "distillery.distilleries_list", username=current_user.username.lower()
            )
        )

    return render_template(
        "distillery/distillery_edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Distillery",
        distillery=_distillery,
        form=form,
    )


@distillery.route("/distillery/<string:distillery_id>", methods=["GET", "POST"])
def distillery_detail(distillery_id: str):
    dt_list_length = request.cookies.get("dt-list-length", "50")
    _distillery = db.get_or_404(Distillery, distillery_id)
    user = _distillery.user

    stmt = (
        select(Bottle)
        .join(Bottle.distilleries)
        .filter(Bottle.user_id == user.id, Distillery.id == distillery_id)
    )
    _bottles = db.session.scalars(stmt).all()

    if request.method == "POST":
        if bool(int(request.form.get("random_toggle"))):
            # Return a random bottle.
            # Cannot be a killed bottle. Template expects a list, so wrap in a list.
            if _bottles.count() > 0:
                has_killed_bottles = False

                bottles_to_list = [
                    db.session.execute(
                        select(Bottle).filter_by(
                            Bottle.date_killed.is_(None),
                            Bottle.distillery_id == distillery_id,
                            Bottle.user_id == current_user.get_id(),
                        )
                    )
                    .order_by(func.rand())
                    .first()
                ]
    else:
        bottles_to_list = _bottles
        has_killed_bottles = len([b for b in _bottles if b.date_killed]) > 0

    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == _distillery.user.username.lower()
    )

    response = make_response(
        render_template(
            "distillery_detail.html",
            title=f"{_distillery.user.username}'s Whiskies: {_distillery.name}",
            has_datatable=True,
            user=_distillery.user,
            is_my_list=is_my_list,
            distillery=_distillery,
            bottles=bottles_to_list,
            has_killed_bottles=has_killed_bottles,
            dt_list_length=dt_list_length,
        )
    )

    response.set_cookie(
        "dt-list-length",
        value=dt_list_length,
        expires=datetime.now() + relativedelta(years=1),
    )
    return response


@distillery.route("/distillery_delete/<string:distillery_id>")
@login_required
def distillery_delete(distillery_id: str):
    _distillery = db.get_or_404(Distillery, distillery_id)

    if len(_distillery.bottles) > 0:
        flash(
            f'You cannot delete "{_distillery.name}", because it has bottles associated to it.',
            "danger",
        )
        return redirect(
            url_for(
                "distillery.distilleries_list", username=current_user.username.lower()
            )
        )
    db.session.delete(_distillery)
    db.session.commit()
    flash(f'"{_distillery.name}" has been successfully deleted.', "success")
    return redirect(
        url_for("distillery.distilleries_list", username=current_user.username.lower())
    )
