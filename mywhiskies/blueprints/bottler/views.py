import random
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from mywhiskies.blueprints.bottler.forms import BottlerEditForm, BottlerForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

bottler = Blueprint("bottler", __name__, template_folder="templates")


@bottler.route("/<username>/bottlers", endpoint="bottlers_list", strict_slashes=False)
def bottlers_list(username: str):
    dt_list_length = request.cookies.get("bt-list-length", "50")
    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )
    user = db.one_or_404(db.select(User).filter_by(username=username))
    response = make_response(
        render_template(
            "bottler/bottler_list.html",
            title=f"{user.username}'s Whiskies: Bottlers",
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


@bottler.route("/bottler/add", methods=["GET", "POST"])
@login_required
def bottler_add():
    form = BottlerForm()
    if request.method == "POST" and form.validate_on_submit():
        bottler_in = Bottler(user_id=current_user.id)
        form.populate_obj(bottler_in)
        db.session.add(bottler_in)
        db.session.commit()
        flash(f'"{bottler_in.name}" has been successfully added.', "success")
        return redirect(url_for("core.home", username=current_user.username.lower()))
    return render_template(
        "bottler/bottler_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottler",
        user=current_user,
        form=form,
    )


@bottler.route("/bottler/edit/<string:bottler_id>", methods=["GET", "POST"])
@login_required
def bottler_edit(bottler_id: str):
    _bottler = db.get_or_404(Bottler, bottler_id)
    form = BottlerEditForm()
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_bottler)
        db.session.add(_bottler)
        db.session.commit()
        flash(f'"{_bottler.name}" has been successfully updated.', "success")
        return redirect(
            url_for("bottler.bottlers_list", username=current_user.username.lower())
        )
    else:
        form = BottlerEditForm(obj=_bottler)
        return render_template(
            "bottler/bottler_edit.html",
            title=f"{current_user.username}'s Whiskies: Edit Bottler",
            bottler=_bottler,
            form=form,
        )


@bottler.route("/bottler/<string:bottler_id>", methods=["GET", "POST"])
def bottler_detail(bottler_id: str):
    dt_list_length = request.cookies.get("dt-list-length", "50")
    _bottler = db.get_or_404(Bottler, bottler_id)
    _bottles = _bottler.bottles
    if request.method == "POST":
        if bool(int(request.form.get("random_toggle"))):
            if len(_bottles) > 0:
                has_killed_bottles = False
                live_bottles = [
                    bottle for bottle in _bottles if bottle.date_killed is None
                ]
                bottles_to_list = [random.choice(live_bottles)]
    else:
        bottles_to_list = _bottles
        has_killed_bottles = len([b for b in _bottles if b.date_killed]) > 0
    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == _bottler.user.username.lower()
    )
    response = make_response(
        render_template(
            "bottler/bottler_detail.html",
            title=f"{_bottler.user.username}'s Whiskies: {_bottler.name}",
            has_datatable=True,
            user=_bottler.user,
            is_my_list=is_my_list,
            bottler=_bottler,
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


@bottler.route("/bottler/delete/<string:bottler_id>")
@login_required
def bottler_delete(bottler_id: str):
    _bottler = db.get_or_404(Bottler, bottler_id)

    if len(_bottler.bottles) > 0:
        flash(
            f'You cannot delete "{_bottler.name}", because it has bottles associated to it.',
            "danger",
        )
        return redirect(
            url_for("bottler.bottlers_list", username=current_user.username.lower())
        )
    db.session.delete(_bottler)
    db.session.commit()
    flash(f'"{_bottler.name}" has been successfully deleted.', "success")
    return redirect(
        url_for("bottler.bottlers_list", username=current_user.username.lower())
    )
