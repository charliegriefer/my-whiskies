from flask import make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.blueprints.bottler.forms import BottlerEditForm, BottlerForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    get_bottler_detail,
    list_bottlers,
)


@bottler_bp.route(
    "/<username>/bottlers", endpoint="bottlers_list", strict_slashes=False
)
def bottlers(username: str):
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = list_bottlers(user, current_user)
    utils.set_cookie_expiration(
        response, "dt_list_length", request.cookies.get("bt-list-length", "50")
    )
    return response


@bottler_bp.route("/bottler/<string:bottler_id>", methods=["GET", "POST"])
def bottler_detail(bottler_id: str):
    context = get_bottler_detail(bottler_id, request, current_user)
    response = make_response(render_template("bottler/bottler_detail.html", **context))
    utils.set_cookie_expiration(response, "dt-list-length", context["dt_list_length"])
    return response


@bottler_bp.route("/bottler/add", methods=["GET", "POST"])
@login_required
def bottler_add():
    form = BottlerForm()

    if form.validate_on_submit():
        add_bottler(form, current_user)
        return redirect(url_for("core.home", username=current_user.username.lower()))

    return render_template(
        "bottler/bottler_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottler",
        user=current_user,
        form=form,
    )


@bottler_bp.route("/bottler/edit/<string:bottler_id>", methods=["GET", "POST"])
@login_required
def bottler_edit(bottler_id: str):
    bottler = db.get_or_404(Bottler, bottler_id)
    form = BottlerEditForm(obj=bottler if request.method != "POST" else None)
    edit_bottler(form, bottler)

    if form.validate_on_submit():
        return redirect(
            url_for("bottler.bottlers_list", username=current_user.username)
        )

    return render_template(
        "bottler/bottler_edit.html",
        title=f"{current_user.username}'s Whiskies: Edit Bottler",
        bottler=bottler,
        form=form,
    )


@bottler_bp.route("/bottler/delete/<string:bottler_id>")
@login_required
def bottler_delete(bottler_id: str):
    delete_bottler(bottler_id, current_user)
    return redirect(url_for("bottler.bottlers_list", username=current_user.username))
