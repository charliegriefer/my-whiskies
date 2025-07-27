from flask import redirect, render_template, request, url_for
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


@bottler_bp.route("/<string:username>/bottlers", endpoint="list")
def bottlers(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_bottlers(user, current_user, request, "bottlers")
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("bt-list-length", "50")
    )
    return response


@bottler_bp.route(
    "/bottler/<string:bottler_id>", methods=["GET", "POST"], endpoint="detail"
)
def bottler(bottler_id: str):
    bottler = db.one_or_404(db.select(Bottler).filter_by(id=bottler_id))
    response = get_bottler_detail(bottler, request, current_user)
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
    "/bottler/edit/<string:bottler_id>", methods=["GET", "POST"], endpoint="edit"
)
@login_required
def bottler_edit(bottler_id: str):
    bottler = db.get_or_404(Bottler, bottler_id)
    form = BottlerEditForm(obj=bottler)

    if form.validate_on_submit():
        edit_bottler(form, bottler)
        return redirect(url_for("bottler.list", username=current_user.username))

    return render_template(
        "bottler/edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottler",
        bottler=bottler,
        form=form,
    )


@bottler_bp.route("/bottler/delete/<string:bottler_id>", endpoint="delete")
@login_required
def bottler_delete(bottler_id: str):
    delete_bottler(current_user, bottler_id)
    return redirect(url_for("bottler.list", username=current_user.username))
