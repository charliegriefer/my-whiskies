from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.blueprints.bottler.forms import BottlerAddForm, BottlerEditForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.common.decorators import validate_username
from mywhiskies.extensions import db
from mywhiskies.services import utils
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    get_bottler_detail,
    list_bottlers,
)


@bottler_bp.route("/<string:username>/bottlers", endpoint="bottler_list")
def bottlers(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_bottlers(user, current_user, request, "bottlers")
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("bt-list-length", "50")
    )
    return response


@bottler_bp.route(
    "/<string:username>/bottler/<string:bottler_id>", methods=["GET", "POST"]
)
def bottler_detail(username: str, bottler_id: str):
    bottler = db.one_or_404(db.select(Bottler).filter_by(id=bottler_id))
    response = get_bottler_detail(bottler, request, current_user)
    utils.set_cookie_expiration(
        response, "dt-list-length", request.cookies.get("dt-list-length", "50")
    )
    return response


@bottler_bp.route("/<string:username>/bottler/add", methods=["GET", "POST"])
@login_required
@validate_username
def bottler_add(username: str):
    form = BottlerAddForm()

    if form.validate_on_submit():
        add_bottler(form, current_user)
        return redirect(url_for("core.main"))

    return render_template(
        "bottler/bottler_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottler",
        user=current_user,
        form=form,
    )


@bottler_bp.route(
    "/<string:username>/bottler/edit/<string:bottler_id>", methods=["GET", "POST"]
)
@login_required
@validate_username
def bottler_edit(username: str, bottler_id: str):
    bottler = db.get_or_404(Bottler, bottler_id)
    form = BottlerEditForm(obj=bottler)

    if form.validate_on_submit():
        edit_bottler(form, bottler)
        return redirect(url_for("bottler.bottler_list", username=current_user.username))

    return render_template(
        "bottler/bottler_edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottler",
        bottler=bottler,
        form=form,
    )


@bottler_bp.route("/<string:username>/bottler/delete/<string:bottler_id>")
@login_required
@validate_username
def bottler_delete(username: str, bottler_id: str):
    delete_bottler(current_user, bottler_id)
    return redirect(url_for("bottler.bottler_list", username=current_user.username))
