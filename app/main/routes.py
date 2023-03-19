import json
import os
import random
import time
from datetime import datetime

import boto3
from dateutil.relativedelta import relativedelta
from flask import current_app, flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import insert
from sqlalchemy.sql.expression import func

from app.extensions import db
from app.main import handler as main_handler
from app.main import main_blueprint
from app.main.forms import BottleForm, BottleEditForm, DistilleryForm, DistilleryEditForm
from app.models import Bottle, BottleTypes, Distillery, User


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
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

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


@main_blueprint.route("/home", endpoint="home")
@login_required
def home():
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

    response = make_response(render_template("home.html",
                                             title=f"{current_user.username}'s Whiskies",
                                             cookie_exists=cookie_exists))
    if not cookie_exists:
        response.set_cookie("my-whiskies-user", str(time.time()))
    return response


# DISTILLERIES
# ######################################################################################################################


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
        return redirect(url_for("main.home"))

    if not request.referrer:
        return redirect(url_for("main.home"))

    json_file = os.path.join(current_app.static_folder, "data", "base_distilleries.json")
    with open(json_file, "r") as f:
        data = json.load(f)

        base_distilleries = data.get("distilleries")
        [d.__setitem__("user_id", current_user.id) for d in base_distilleries]

        db.session.execute(insert(Distillery), base_distilleries)
        db.session.commit()

    flash(f"{len(base_distilleries)} distilleries have been added to your account.")
    return redirect(url_for("main.home"))


@main_blueprint.route("/distilleries", endpoint="list_distilleries")
@login_required
def list_distilleries():
    """ Don't need a big docstring here. This endpoint lists a user's distilleries. """
    dt_list_length = request.cookies.get("dt-list-length", "50")

    response = make_response(render_template("distillery_list.html",
                                             title=f"{current_user.username}'s Distilleries",
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
        return redirect(url_for("main.home"))
    return render_template("distillery_add.html",
                           title=f"{current_user.username}'s Whiskies | Add Distillery",
                           user=current_user,
                           form=form)


@main_blueprint.route("/distillery_edit/<string:distillery_id>", methods=["GET", "POST"])
@login_required
def distillery_edit(distillery_id: str):
    _distillery = Distillery.query.get_or_404(distillery_id)
    form = DistilleryEditForm()

    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_distillery)

        db.session.add(_distillery)
        db.session.commit()
        flash(f"\"{_distillery.name}\" has been successfully updated.", "success")
        return redirect(url_for("main.list_distilleries"))
    else:
        form = DistilleryEditForm(obj=_distillery)
        return render_template("distillery_edit.html",
                               title=f"Edit Distillery {_distillery.name}",
                               distillery=_distillery,
                               form=form)


@main_blueprint.route("/distillery_delete/<string:distillery_id>")
@login_required
def distillery_delete(distillery_id: str):
    _distillery = Distillery.query.get_or_404(distillery_id)

    if len(_distillery.bottles) > 0:
        flash(f"You cannot delete \"{_distillery.name}\", because it has bottles associated to it.", "danger")
        return redirect(url_for("main.distilleries"))
    db.session.delete(_distillery)
    db.session.commit()
    flash(f"\"{_distillery.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.list_distilleries"))


# BOTTLES
# ######################################################################################################################


@main_blueprint.route("/<username>", methods=["GET", "POST"], endpoint="list_bottles")
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

    all_bottles = Bottle.query.filter(Bottle.user_id == user.id)

    if request.method == "POST":
        active_bottle_types = request.form.getlist("bottle_type")  # checked bottle types to show

        if len(active_bottle_types):
            bottles_to_list = all_bottles.filter(Bottle.type.in_(active_bottle_types)).all()
            if bool(int(request.form.get("random_toggle"))):
                if len(bottles_to_list) == 0:
                    bottles_to_list = []
                else:
                    bottles_to_list = [random.choice(bottles_to_list)]
        else:
            bottles_to_list = []

    else:
        active_bottle_types = [bt.name for bt in BottleTypes]
        bottles_to_list = all_bottles.all()

    is_my_list = current_user.is_authenticated and current_user.username.lower() == username.lower()

    response = make_response(render_template("bottle_list.html",
                                             title=f"{user.username}'s Whiskies",
                                             user=user,
                                             bottles=bottles_to_list,
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
    return render_template("bottle_detail.html", bottle=_bottle, is_my_bottle=is_my_bottle)


@main_blueprint.route("/bottle_add", methods=["GET", "POST"])
@login_required
def bottle_add():
    form = main_handler.prep_bottle_form(current_user, BottleForm())

    if request.method == "POST" and form.validate_on_submit():
        bottle_in = Bottle(user_id=current_user.id)
        form.populate_obj(bottle_in)
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
        return redirect(url_for("main.home"))

    return render_template("bottle_add.html", form=form)


@main_blueprint.route("/bottle_edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    _bottle = Bottle.query.get_or_404(bottle_id)
    form = main_handler.prep_bottle_form(current_user, BottleEditForm(obj=_bottle))

    if request.method == "POST" and form.validate_on_submit():
        form.populate_obj(_bottle)

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
        return redirect(url_for("main.home"))

    else:
        form.type.data = _bottle.type.name
        return render_template("bottle_edit.html",
                               title=f"Edit {_bottle.name}",
                               bottle=_bottle, form=form)


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
    return redirect(url_for("main.list_bottles", username=current_user.username))


@main_blueprint.route("/terms")
def terms():
    return render_template("tos.html")


@main_blueprint.route("/privacy")
def privacy():
    return render_template("tos_privacy.html")


@main_blueprint.route("/cookies")
def cookies():
    return render_template("tos_cookies.html")
