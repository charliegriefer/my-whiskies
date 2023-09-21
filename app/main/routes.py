import json
import os
import random
import time
from datetime import datetime

import boto3
import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import current_app, flash, make_response, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import insert
from sqlalchemy.sql.expression import func

from app.extensions import db
from app.main import handler as main_handler
from app.main import main_blueprint
from app.main.forms import BottleForm, BottleEditForm, BottlerForm, BottlerEditForm, DistilleryForm, DistilleryEditForm
from app.models import Bottle, Bottler, BottleTypes, Distillery, User


@main_blueprint.route("/")
@main_blueprint.route("/index")
def index():
    """
    Unauthenticated home page.
    ---
    get:
        summary: Unauthenticated home page endpoint.
        description: Details about the site. Some stats for fun.
        parameters:
            - n/a
        responses:
            200:
                description: Nothing to see here.
    """
    # if current_user.is_authenticated:
    #     return redirect(url_for("main.home", username=current_user.username.lower()))

    user_count = User.query.filter(User.email_confirmed == 1).count()

    distillery_count = Distillery.query.with_entities(Distillery.name).order_by(Distillery.name)
    distillery_count = distillery_count.group_by(Distillery.name).count()
    bottle_count = Bottle.query.count()
    pic_count = Bottle.query.with_entities(func.sum(Bottle.image_count)).scalar()

    bt_counts = Bottle.query.with_entities(Bottle.type,
                                           func.count(Bottle.type)).order_by(Bottle.type).group_by(Bottle.type)

    bottle_type_counts = {i.value: 0 for i in BottleTypes}
    [bottle_type_counts.__setitem__(f[0].value, f[1]) for f in bt_counts]

    return render_template("index.html",
                           title="My Whiskies Online",
                           user_count=user_count,
                           pic_count=pic_count,
                           distillery_count=distillery_count,
                           bottle_count=bottle_count,
                           bottle_type_counts=bottle_type_counts)


@main_blueprint.route("/<string:username>", endpoint="home")
def home(username: str):
    """
    Authenticated home page.
    ---
    get:
        summary: Authenticated home page endpoint.
        description: Stats about the user. Distilleries, bottles.
        parameters:
            - na/
        responses:
            200:
                description: User's distillery counts and bottle counts to be returned.
    """
    cookie_exists = request.cookies.get("my-whiskies-user", None)

    if current_user.is_authenticated:
        user = current_user
        is_my_home = current_user.username.lower() == username.lower()
    else:
        user = User.query.filter(User.username == username).first_or_404()
        is_my_home = False

    live_bottles = [bottle for bottle in user.bottles if bottle.date_killed is None]

    response = make_response(render_template("home.html",
                                             title=f"{user.username}'s Whiskies",
                                             user=user,
                                             live_bottles=live_bottles,
                                             is_my_home=is_my_home,
                                             cookie_exists=cookie_exists))
    if not cookie_exists:
        response.set_cookie("my-whiskies-user", str(time.time()))
    return response


# BOTTLERS
# #####################################################################################################################
@main_blueprint.route("/<username>/bottlers", endpoint="bottlers_list")
def bottlers_list(username: str):
    """ Don't need a big docstring here. This endpoint lists a user's bottlers. """
    dt_list_length = request.cookies.get("bt-list-length", "50")
    is_my_list = current_user.is_authenticated and current_user.username.lower() == username.lower()
    user = User.query.filter(User.username == username).first_or_404()

    response = make_response(render_template("bottler_list.html",
                                             title=f"{user.username}'s Whiskies: Bottlers",
                                             is_my_list=is_my_list,
                                             user=user,
                                             dt_list_length=dt_list_length))
    response.set_cookie("dt-list-length", value=dt_list_length, expires=datetime.now() + relativedelta(years=1))
    return response


@main_blueprint.route("/bottler_add", methods=["GET", "POST"])
@login_required
def bottler_add():
    form = BottlerForm()
    if request.method == "POST" and form.validate_on_submit():
        bottler_in = Bottler(user_id=current_user.id)
        form.populate_obj(bottler_in)
        db.session.add(bottler_in)
        db.session.commit()
        flash(f"\"{bottler_in.name}\" has been successfully added.", "success")
        return redirect(url_for("main.home", username=current_user.username.lower()))
    return render_template("bottler_add.html",
                           title=f"{current_user.username}'s Whiskies: Add Bottler",
                           user=current_user,
                           form=form)


@main_blueprint.route("/bottler_edit/<string:bottler_id>", methods=["GET", "POST"])
@login_required
def bottler_edit(bottler_id: str):
    _bottler = Bottler.query.get_or_404(bottler_id)
    form = BottlerEditForm()

    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_bottler)

        db.session.add(_bottler)
        db.session.commit()
        flash(f"\"{_bottler.name}\" has been successfully updated.", "success")
        return redirect(url_for("main.bottlers_list", username=current_user.username.lower()))
    else:
        form = BottlerEditForm(obj=_bottler)
        return render_template("bottler_edit.html",
                               title=f"{current_user.username}'s Whiskies: Edit Bottler",
                               bottler=_bottler,
                               form=form)


@main_blueprint.route("/bottler/<string:bottler_id>", methods=["GET", "POST"])
def bottler_detail(bottler_id: str):
    dt_list_length = request.cookies.get("dt-list-length", "50")
    _bottler = Bottler.query.get_or_404(bottler_id)
    _bottles = Bottle.query.filter(Bottle.bottler_id == bottler_id).filter(Bottle.user_id == current_user.get_id())

    if request.method == "POST":
        if bool(int(request.form.get("random_toggle"))):
            if _bottles.count() > 0:
                has_killed_bottles = False
                bottles_to_list = [Bottle.query.filter(Bottle.date_killed.is_(None))
                                               .filter(Bottle.bottler_id == bottler_id)
                                               .filter(Bottle.user_id == current_user.get_id())
                                               .order_by(func.rand()).first()]
    else:
        bottles_to_list = _bottles
        has_killed_bottles = len([b for b in _bottles if b.date_killed]) > 0

    is_my_list = current_user.is_authenticated and current_user.username.lower() == _bottler.user.username.lower()

    response = make_response(render_template("bottler_detail.html",
                           title=f"{_bottler.user.username}'s Whiskies: {_bottler.name}",
                           user=_bottler.user,
                           is_my_list=is_my_list,
                           bottler=_bottler,
                           bottles=bottles_to_list,
                           has_killed_bottles=has_killed_bottles,
                           dt_list_length=dt_list_length))

    response.set_cookie("dt-list-length", value=dt_list_length, expires=datetime.now() + relativedelta(years=1))
    return response


@main_blueprint.route("/bottler_delete/<string:bottler_id>")
@login_required
def bottler_delete(bottler_id: str):
    _bottler = Bottler.query.get_or_404(bottler_id)

    if len(_bottler.bottles) > 0:
        flash(f"You cannot delete \"{_bottler.name}\", because it has bottles associated to it.", "danger")
        return redirect(url_for("main.bottlers_list", username=current_user.username.lower()))
    db.session.delete(_bottler)
    db.session.commit()
    flash(f"\"{_bottler.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.bottlers_list", username=current_user.username.lower()))


# DISTILLERIES
# #####################################################################################################################
@main_blueprint.route("/bulk_distillery_add")
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
        return redirect(url_for("main.home", username=current_user.username.lower()))

    if not request.referrer:
        return redirect(url_for("main.home", username=current_user.username.lower()))

    json_file = os.path.join(current_app.static_folder, "data", "base_distilleries.json")
    with open(json_file, "r") as f:
        data = json.load(f)

        base_distilleries = data.get("distilleries")
        [d.__setitem__("user_id", current_user.id) for d in base_distilleries]

        db.session.execute(insert(Distillery), base_distilleries)
        db.session.commit()

    flash(f"{len(base_distilleries)} distilleries have been added to your account.")
    return redirect(url_for("main.home", username=current_user.username.lower()))


@main_blueprint.route("/<username>/distilleries", endpoint="distilleries_list")
def distilleries_list(username: str):
    """ Don't need a big docstring here. This endpoint lists a user's distilleries. """
    dt_list_length = request.cookies.get("dt-list-length", "50")
    is_my_list = current_user.is_authenticated and current_user.username.lower() == username.lower()
    user = User.query.filter(User.username == username).first_or_404()

    response = make_response(render_template("distillery_list.html",
                                             title=f"{user.username}'s Whiskies: Distilleries",
                                             is_my_list=is_my_list,
                                             user=user,
                                             dt_list_length=dt_list_length))
    response.set_cookie("dt-list-length", value=dt_list_length, expires=datetime.now() + relativedelta(years=1))
    return response


@main_blueprint.route("/distillery_add", methods=["GET", "POST"])
@login_required
def distillery_add():
    form = DistilleryForm()

    if request.method == "POST" and form.validate_on_submit():
        distillery_in = Distillery(user_id=current_user.id)
        form.populate_obj(distillery_in)
        db.session.add(distillery_in)
        db.session.commit()
        flash(f"\"{distillery_in.name}\" has been successfully added.", "success")
        return redirect(url_for("main.home", username=current_user.username.lower()))
    return render_template("distillery_add.html",
                           title=f"{current_user.username}'s Whiskies: Add Distillery",
                           user=current_user,
                           form=form)


@main_blueprint.route("/distillery_edit/<string:distillery_id>", methods=["GET", "POST"])
@login_required
def distillery_edit(distillery_id: str):
    _distillery = Distillery.query.get_or_404(distillery_id)
    form = DistilleryEditForm(obj=_distillery)
    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_distillery)

        db.session.add(_distillery)
        db.session.commit()
        flash(f"\"{_distillery.name}\" has been successfully updated.", "success")
        return redirect(url_for("main.distilleries_list", username=current_user.username.lower()))

    return render_template("distillery_edit.html",
                            title=f"{current_user.username}'s Whiskies: Edit Distillery",
                            distillery=_distillery,
                            form=form)


@main_blueprint.route("/distillery/<string:distillery_id>", methods=["GET", "POST"])
def distillery_detail(distillery_id: str):
    dt_list_length = request.cookies.get("dt-list-length", "50")
    _distillery = Distillery.query.get_or_404(distillery_id)
    _bottles = Bottle.query.filter(Bottle.distillery_id == distillery_id).filter(Bottle.user_id == current_user.get_id())

    if request.method == "POST":
        if bool(int(request.form.get("random_toggle"))):
            if _bottles.count() > 0:
                has_killed_bottles = False
                bottles_to_list = [Bottle.query.filter(Bottle.date_killed.is_(None))
                                               .filter(Bottle.distillery_id == distillery_id)
                                               .filter(Bottle.user_id == current_user.get_id())
                                               .order_by(func.rand()).first()]
    else:
        bottles_to_list = _bottles
        has_killed_bottles = len([b for b in _bottles if b.date_killed]) > 0

    is_my_list = current_user.is_authenticated and current_user.username.lower() == _distillery.user.username.lower()

    response = make_response(render_template("distillery_detail.html",
                           title=f"{_distillery.user.username}'s Whiskies: {_distillery.name}",
                           user=_distillery.user,
                           is_my_list=is_my_list,
                           distillery=_distillery,
                           bottles=bottles_to_list,
                           has_killed_bottles=has_killed_bottles,
                           dt_list_length=dt_list_length))

    response.set_cookie("dt-list-length", value=dt_list_length, expires=datetime.now() + relativedelta(years=1))
    return response


@main_blueprint.route("/distillery_delete/<string:distillery_id>")
@login_required
def distillery_delete(distillery_id: str):
    _distillery = Distillery.query.get_or_404(distillery_id)

    if len(_distillery.bottles) > 0:
        flash(f"You cannot delete \"{_distillery.name}\", because it has bottles associated to it.", "danger")
        return redirect(url_for("main.distilleries_list", username=current_user.username.lower()))
    db.session.delete(_distillery)
    db.session.commit()
    flash(f"\"{_distillery.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.distilleries_list", username=current_user.username.lower()))


# BOTTLES
# #####################################################################################################################


@main_blueprint.route("/<username>/bottles", methods=["GET", "POST"], endpoint="list_bottles")
def bottles(username: str):
    """
    List a User's Bottles.
    ---
    get:
        summary: Lists all of a user's bottles.
        description: A datatable list of a user's bottles.
        parameters:
            - na
        responses:
            200:
                description: A full list of all of a user's bottles.
    post:
        summary: Lists a user's bottles optionally filtered by type. Optionally a single random bottle.
        description: If method is post, form data is assumed present.
                     Bottles are filtered on that form data.
        parameters:
            - bottle.type (american whiskey, bourbon, rye, etc)
            - random_toggle: If true, returns a random record from the existing bottle list
    """
    dt_list_length = request.cookies.get("dt-list-length", "50")
    user = User.query.filter(User.username == username).first_or_404()

    all_bottles = user.bottles
    killed_bottles = [b for b in all_bottles if b.date_killed]

    if request.method == "POST":
        active_bottle_types = request.form.getlist("bottle_type")  # checked bottle types to show

        if len(active_bottle_types):
            bottles_to_list = [b for b in all_bottles if b.type.name in active_bottle_types]
            if bool(int(request.form.get("random_toggle"))):
                if len(bottles_to_list) > 0:
                    bottles_to_list = [random.choice(bottles_to_list)]
        else:
            bottles_to_list = []

    else:
        active_bottle_types = [bt.name for bt in BottleTypes]
        bottles_to_list = all_bottles

    is_my_list = current_user.is_authenticated and current_user.username.lower() == username.lower()

    response = make_response(render_template("bottle_list.html",
                                             title=f"{user.username}'s Whiskies: Bottles",
                                             user=user,
                                             bottles=bottles_to_list,
                                             has_killed_bottles=bool(len(killed_bottles)),
                                             bottle_types=BottleTypes,
                                             active_filters=active_bottle_types,
                                             dt_list_length=dt_list_length,
                                             is_my_list=is_my_list))

    response.set_cookie("dt-list-length", value=dt_list_length, expires=datetime.now() + relativedelta(years=1))
    return response


@main_blueprint.route("/bottle/<bottle_id>")
def bottle_detail(bottle_id: str):
    _bottle = Bottle.query.get_or_404(bottle_id)
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    return render_template("bottle_detail.html",
                           title=f"{_bottle.user.username}'s Whiskies: {_bottle.name}",
                           bottle=_bottle,
                           user=_bottle.user,
                           ts=time.time(),
                           is_my_bottle=is_my_bottle)


@main_blueprint.route("/bottle_add", methods=["GET", "POST"])
@login_required
def bottle_add():
    form = main_handler.prep_bottle_form(current_user, BottleForm())

    if request.method == "POST" and form.validate_on_submit():
        bottle_in = Bottle(user_id=current_user.id)
        form.populate_obj(bottle_in)

        # handle "Distillery Bottling"
        if bottle_in.bottler_id == "0":
            bottle_in.bottler_id = None

        db.session.add(bottle_in)
        db.session.commit()

        db.session.flush()  # to get the id of the newly created bottle
        flash_message = f"\"{bottle_in.name}\" has been successfully added."
        flash_category = "success"

        image_upload_success = main_handler.bottle_add_images(form, bottle_in)

        if image_upload_success:
            pass
        else:
            flash_message = f"An error occurred while creating \"{bottle_in.name}\"."
            flash_category = "danger"
            Bottle.query.get(bottle_in.id).delete()

        bottle_in.image_count = main_handler.get_bottle_image_count(bottle_in.id)

        db.session.commit()

        flash(flash_message, flash_category)
        return redirect(url_for("main.home", username=current_user.username.lower()))

    return render_template("bottle_add.html",
                           title=f"{current_user.username}'s Whiskies: Add Bottle",
                           form=form)


@main_blueprint.route("/bottle_edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    _bottle = Bottle.query.get_or_404(bottle_id)
    form = main_handler.prep_bottle_form(current_user, BottleEditForm(obj=_bottle))

    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_bottle)

        # handle "Distillery Bottling"
        if _bottle.bottler_id == "0":
            _bottle.bottler_id = None

        main_handler.bottle_edit_images(form, _bottle)
        image_upload_success = main_handler.bottle_add_images(form, _bottle)

        if image_upload_success:
            main_handler.bottle_delete_images(_bottle)
            flash_message = f"\"{_bottle.name}\" has been successfully updated."
            flash_category = "success"
            _bottle.image_count = main_handler.get_bottle_image_count(_bottle.id)
            db.session.add(_bottle)
            db.session.commit()
        else:
            flash_message = f"An error occurred while updating \"{_bottle.name}\"."
            flash_category = "danger"

        flash(flash_message, flash_category)
        return redirect(url_for("main.home", username=current_user.username.lower()))

    else:
        form.type.data = _bottle.type.name
        return render_template("bottle_edit.html",
                               title=f"{current_user.username}'s Whiskies: Edit Bottle",
                               ts=time.time(),
                               bottle=_bottle,
                               form=form)


@main_blueprint.route("/bottle_delete/<string:bottle_id>")
@login_required
def bottle_delete(bottle_id: str):
    bottle_to_delete = Bottle.query.get_or_404(bottle_id)

    db.session.delete(bottle_to_delete)

    if bottle_to_delete.image_count:
        s3_client = boto3.client("s3")
        for i in range(1, bottle_to_delete.image_count + 1):
            s3_client.delete_object(Bucket="my-whiskies-pics", Key=f"{bottle_to_delete.id}_{i}.png")
    db.session.commit()

    flash(f"\"{bottle_to_delete.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.list_bottles", username=current_user.username.lower()))


@main_blueprint.route("/export_data/<string:user_id>")
@login_required
def export_data(user_id: str):
    user = User.query.get_or_404(user_id)

    fieldnames = ["Bottle Name", "Bottle Type", "Distillery", "Year", "ABV", "Description",
                  "Review", "Stars", "Cost", "Date Purchased", "Date Opened", "Date Killed"]

    _bottles = []
    for _bottle in user.bottles:
        _bottles.append([_bottle.name,
                         _bottle.type.value,
                         _bottle.distillery.name,
                         _bottle.year,
                         _bottle.abv,
                         _bottle.description,
                         _bottle.review,
                         _bottle.stars,
                         _bottle.cost,
                         _bottle.date_purchased,
                         _bottle.date_opened,
                         _bottle.date_killed])

    df = pd.DataFrame(_bottles, columns=fieldnames)
    df = df.sort_values(by=["Bottle Name"])
    df.to_csv(f"/tmp/{user_id}.csv", index=False)

    return send_file(f"/tmp/{user_id}.csv",
                     as_attachment=True,
                     mimetype="text/csv",
                     download_name=f"my_whiskies_{user.username.lower()}.csv")


@main_blueprint.route("/terms")
def terms():
    return render_template("tos.html")


@main_blueprint.route("/privacy")
def privacy():
    return render_template("tos_privacy.html")


@main_blueprint.route("/cookies")
def cookies():
    return render_template("tos_cookies.html")
