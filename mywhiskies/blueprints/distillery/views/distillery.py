from flask import current_app, flash, redirect, render_template, request, url_for
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


@distillery_bp.route("/<username>/distilleries", endpoint="list")
def distilleries(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_distilleries(user, current_user, request, "distilleries")
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("bt-list-length", "50")
    )
    return response


@distillery_bp.route(
    "/distillery/<string:distillery_id>", methods=["GET", "POST"], endpoint="detail"
)
def distillery_detail(distillery_id: str):
    distillery = db.one_or_404(db.select(Distillery).filter_by(id=distillery_id))
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
    "/distillery_edit/<string:distillery_id>", methods=["GET", "POST"], endpoint="edit"
)
@login_required
def distillery_edit(distillery_id: str):
    distillery = db.get_or_404(Distillery, distillery_id)
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


@distillery_bp.route("/distillery_delete/<string:distillery_id>", endpoint="delete")
@login_required
def distillery_delete(distillery_id: str):
    delete_distillery(current_user, distillery_id)
    return redirect(url_for("distillery.list", username=current_user.username))
