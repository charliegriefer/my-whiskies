import io
import time

import boto3
from PIL import Image
from botocore.exceptions import ClientError
from flask import flash, make_response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import insert
from sqlalchemy.sql.expression import func

from app.extensions import db
from app.main import main_blueprint
from app.main.forms import BottleForm, BottleEditForm, DistilleryForm, DistilleryEditForm
from app.models import User
from app.models.bottle import Bottle, BottleTypes, Distillery


@main_blueprint.route("/")
def home():
    cookie_exists = request.cookies.get("my-whiskies-user", None)

    if current_user.is_authenticated:
        my_bottles = Bottle.query.filter(Bottle.user_id == current_user.id).all()
        my_distilleries = Distillery.query.filter(Distillery.user_id == current_user.id).all()

        resp = make_response(render_template("home.html",
                                             title=f"{current_user.username}'s Whiskies| Home Page",
                                             user=current_user,
                                             bottles=my_bottles,
                                             distilleries=my_distilleries,
                                             cookie_exists=cookie_exists))
    else:
        user_count = User.query.count() - 1  # subtract 1 for "admin" user
        distillery_count = Distillery.query.with_entities(Distillery.name).order_by(Distillery.name)
        distillery_count = distillery_count.group_by(Distillery.name).count()
        bottle_count = Bottle.query.count()

        bottles_types = Bottle.query.with_entities(Bottle.type,
                                                   func.count(Bottle.type)).order_by(Bottle.type).group_by(Bottle.type)

        resp = make_response(render_template("index.html",
                                             title="My Whiskies Online| Home Page",
                                             user_count=user_count,
                                             distillery_count=distillery_count,
                                             bottle_count=bottle_count,
                                             bottle_types=bottles_types.all(),
                                             cookie_exists=cookie_exists))

    if not cookie_exists:
        resp.set_cookie("my-whiskies-user", str(time.time()))
    return resp


@main_blueprint.route("/home")
@main_blueprint.route("/index")
def go_home():
    return redirect(url_for("main.home"))


@main_blueprint.route("/add_distilleries")
@login_required
def add_distilleries():
    if request.referrer.split("/")[-1] != "home":
        return redirect(url_for("main.home"))

    if Distillery.query.filter(Distillery.user_id == current_user.id).count() > 0:
        return redirect(url_for("main.home"))

    base_distilleries = [d.__dict__ for d in Distillery.query.filter(Distillery.user_id == 0).all()]
    for _distillery in base_distilleries:
        del _distillery["id"]
        del _distillery["_sa_instance_state"]
        _distillery["user_id"] = current_user.id

    db.session.execute(insert(Distillery), base_distilleries)
    db.session.commit()

    flash(f"{len(base_distilleries)} distilleries have been added to your account.")
    return redirect(url_for("main.home"))


@main_blueprint.route("/distillery", methods=["GET", "POST"])
@login_required
def distillery():
    form = DistilleryForm()
    if request.method == "POST" and form.validate_on_submit():
        distillery_in = Distillery(name=form.name.data.strip(),
                                   description=form.description.data.strip(),
                                   region_1=form.region_1.data.strip(),
                                   region_2=form.region_2.data.strip(),
                                   url=form.url.data.strip(),
                                   user_id=current_user.id)
        db.session.add(distillery_in)
        db.session.commit()
        flash(f"\"{distillery_in.name}\" has been successfully added.", "success")
        return redirect(url_for("main.home"))
    return render_template("distillery_add.html",
                           title=f"{current_user.username}'s Whiskies | Add Distillery",
                           user=current_user,
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
    return redirect(url_for("main.list_bottles", username=current_user.username))


@main_blueprint.route("/bottle_edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    if request.method == "GET":
        _bottle = Bottle.query.get_or_404(bottle_id)
        form = BottleEditForm(obj=_bottle)
    else:
        form = BottleEditForm()

    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))
    _distilleries = Distillery.query.filter_by(user_id=current_user.id).order_by("name").all()
    form.distillery.choices = [(x.id, x.name) for x in _distilleries]
    form.distillery.choices.insert(0, ("", "Choose a Distillery"))

    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    if form.year.data:
        form.year.data = int(form.year.data)

    if request.method == "POST" and form.validate_on_submit():
        removed_1 = False
        removed_2 = False

        _bottle = Bottle.query.get(bottle_id)
        s3_client = boto3.client("s3")
        if form.remove_image_1.data:
            s3_client.delete_object(Bucket="my-whiskies-pics", Key=f"{bottle_id}_1.png")
            _bottle.image_count = _bottle.image_count - 1
            removed_1 = True
        if form.remove_image_2.data:
            s3_client.delete_object(Bucket="my-whiskies-pics", Key=f"{bottle_id}_2.png")
            _bottle.image_count = _bottle.image_count - 1
            removed_2 = True
        if form.remove_image_3.data:
            s3_client.delete_object(Bucket="my-whiskies-pics", Key=f"{bottle_id}_3.png")
            _bottle.image_count = _bottle.image_count - 1

        if removed_1 or removed_2:
            bottle_response = s3_client.list_objects_v2(Bucket="my-whiskies-pics", Prefix=f"{bottle_id}_")
            bottle_response_contents = bottle_response.get("Contents")
            bottle_images = [bottle_content.get("Key") for bottle_content in bottle_response_contents]

            for i, bottle_image in enumerate(bottle_images):
                if i + 1 != int(bottle_image.split("_")[-1].split(".")[0]):
                    s3_client.copy_object(Bucket="my-whiskies-pics",
                                          CopySource=f"my-whiskies-pics/{bottle_image}",
                                          Key=f"{bottle_id}_{i + 1}.png")
                    s3_client.delete_object(Bucket="my-whiskies-pics", Key=f"{bottle_image}")

        _bottle.name = form.name.data
        _bottle.type = form.type.data
        if form.year.data:
            _bottle.year = int(form.year.data)
        else:
            _bottle.year = None
        _bottle.abv = float(form.abv.data)
        _bottle.url = form.url.data
        _bottle.description = form.description.data
        _bottle.review = form.review.data
        if form.stars.data:
            _bottle.stars = float(form.stars.data)
        else:
            _bottle.stars = None
        if form.cost.data:
            _bottle.cost = float(form.cost.data)
        _bottle.date_purchased = form.date_purchased.data
        _bottle.date_opened = form.date_opened.data
        _bottle.date_killed = form.date_killed.data
        _bottle.distillery_id = form.distillery.data

        flash_message = f"\"{_bottle.name}\" has been successfully updated."
        flash_category = "success"

        # check images
        for i in range(1, 4):
            image_field = form[f"bottle_image_{i}"]

            if image_field.data:
                image_in = Image.open(image_field.data)
                if image_in.width > 400:
                    divisor = image_in.width/400
                    image_dims = (int(image_in.width/divisor), int(image_in.height/divisor))
                    image_in = image_in.resize(image_dims)

                new_filename = f"{_bottle.id}_{i}"

                in_mem_file = io.BytesIO()
                image_in.save(in_mem_file, format="png")
                in_mem_file.seek(0)

                s3_client = boto3.client("s3")
                try:
                    s3_client.put_object(Body=in_mem_file, Bucket="my-whiskies-pics", Key=f"{new_filename}.png")
                    _bottle.image_count = _bottle.image_count + 1
                except ClientError:
                    flash_message = f"An error occurred while creating \"{_bottle.name}\"."
                    flash_category = "danger"

        db.session.add(_bottle)
        db.session.commit()

        flash(flash_message, flash_category)
        return redirect(url_for("main.list_bottles", username=current_user.username))
    else:
        _bottle = Bottle.query.get(bottle_id)
        form.distillery.data = _bottle.distillery_id
        form.type.data = _bottle.type.name
        form.stars.data = str(_bottle.stars)
        return render_template("bottle_edit.html", bottle=_bottle, user=current_user, form=form)


@main_blueprint.route("/distillery_edit/<string:distillery_id>", methods=["GET", "POST"])
@login_required
def distillery_edit(distillery_id: str):
    form = DistilleryEditForm()
    if request.method == "POST" and form.validate_on_submit():
        _distillery = Distillery.query.get(distillery_id)

        _distillery.name = form.name.data.strip()
        _distillery.description = form.description.data.strip()
        _distillery.region_1 = form.region_1.data.strip()
        _distillery.region_2 = form.region_2.data.strip()
        _distillery.url = form.url.data.strip()

        db.session.add(_distillery)
        db.session.commit()
        flash(f"\"{_distillery.name}\" has been successfully added.", "success")
        return redirect(url_for("main.distilleries"))
    else:
        _distillery = Distillery.query.get_or_404(distillery_id)
        form = DistilleryEditForm(obj=_distillery)
        return render_template("distillery_edit.html", distillery=_distillery, user=current_user, form=form)


@main_blueprint.route("/distillery_delete/<string:distillery_id>")
@login_required
def distillery_delete(distillery_id: str):
    _distillery = Distillery.query.get(distillery_id)
    distillery_bottles = Bottle.query.filter(Bottle.distillery_id == distillery_id).count()
    if distillery_bottles > 0:
        flash(f"You cannot delete \"{_distillery.name}\", because it has bottles associated to it.", "danger")
        return redirect(url_for("main.distilleries"))
    db.session.delete(_distillery)
    db.session.commit()
    flash(f"\"{_distillery.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.distilleries"))


@main_blueprint.route("/distilleries")
@login_required
def distilleries():
    _distilleries = Distillery.query.filter(Distillery.user_id == current_user.id).all()
    return render_template("distillery_list.html", user=current_user, distilleries=_distilleries)


@main_blueprint.route("/bottle", methods=["GET", "POST"])
@login_required
def bottle():
    form = BottleForm()

    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    _distilleries = Distillery.query.filter_by(user_id=current_user.id).order_by("name").all()
    form.distillery.choices = [(x.id, x.name) for x in _distilleries]
    form.distillery.choices.insert(0, ("", "Choose a Distillery"))

    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    # do some pre-processing of the form data
    if form.year.data and form.year.data != "":
        form.year.data = int(form.year.data)
    if form.abv.data and form.abv.data != "":
        form.abv.data = float(form.abv.data)
    if form.cost.data and form.cost.data != "":
        form.cost.data = float(form.cost.data)
    if form.stars.data and form.stars.data != "":
        form.stars.data = float(form.stars.data)

    if request.method == "POST" and form.validate_on_submit():
        bottle_images = 0
        bottle_in = Bottle(name=form.name.data.strip(),
                           type=form.type.data,
                           abv=form.abv.data,
                           cost=form.cost.data,
                           distillery_id=form.distillery.data,
                           user_id=current_user.id)

        if form.year.data and form.year.data != "":
            bottle_in.year = form.year.data
        if form.stars.data and form.stars.data != "":
            bottle_in.stars = form.stars.data
        if form.url.data and form.url.data != "":
            bottle_in.url = form.url.data.strip()
        if form.description.data and form.description.data != "":
            bottle_in.description = form.description.data.strip()
        if form.review.data and form.review.data != "":
            bottle_in.review = form.review.data.strip()

        if form.date_purchased.data and form.date_purchased.data != "":
            bottle_in.date_purchased = form.date_purchased.data
        if form.date_killed.data and form.date_killed.data != "":
            bottle_in.date_killed = form.date_killed.data

        db.session.add(bottle_in)
        db.session.commit()
        db.session.flush()
        flash_message = f"\"{bottle_in.name}\" has been successfully added."
        flash_category = "success"

        # check images
        for i in range(1, 4):
            image_field = form[f"bottle_image_{i}"]

            if image_field.data:
                image_in = Image.open(image_field.data)
                if image_in.width > 400:
                    divisor = image_in.width/400
                    image_dims = (int(image_in.width/divisor), int(image_in.height/divisor))
                    image_in = image_in.resize(image_dims)

                new_filename = f"{bottle_in.id}_{i}"

                in_mem_file = io.BytesIO()
                image_in.save(in_mem_file, format="png")
                in_mem_file.seek(0)

                s3_client = boto3.client("s3")
                try:
                    s3_client.put_object(Body=in_mem_file, Bucket="my-whiskies-pics", Key=f"{new_filename}.png")
                    bottle_images = bottle_images + 1
                except ClientError:
                    flash_message = f"An error occurred while creating \"{bottle_in.name}\"."
                    flash_category = "danger"
                    Bottle.query.filter_by(id=bottle_in.id).delete()
                    db.session.commit()

        bottle_in.image_count = bottle_images
        db.session.commit()

        flash(flash_message, flash_category)
        return redirect(url_for("main.home"))

    return render_template("bottle_add.html", form=form)


@main_blueprint.route("/<username>", methods=["GET", "POST"], endpoint="list_bottles")
def bottle_list(username: str):
    user = User.query.filter(User.username == username).first_or_404()
    bottles = Bottle.query.filter(Bottle.user_id == user.id)

    if request.method == "POST":
        active_bottle_types = request.form.getlist("bottle_type")
        if len(active_bottle_types):
            bottles = bottles.filter(Bottle.type.in_(active_bottle_types))
        else:
            bottles = []
        if request.form.get("random_toggle"):
            bottles = bottles.order_by(func.random())
    else:
        active_bottle_types = [bt.name for bt in BottleTypes]

    if request.form.get("random_toggle"):
        bottles = bottles.first()
        if bottles:
            bottles = [bottles]
        else:
            bottles = []
    else:
        bottles = bottles.all()

    is_my_list = current_user.is_authenticated and current_user.username.lower() == username.lower()

    return render_template("bottle_list.html",
                           title=f"{user.username}'s Whiskies| Bottles",
                           user=user,
                           bottles=bottles,
                           selected_length=request.form.get("bottle_length", 50),
                           bottle_types=BottleTypes,
                           active_filters=active_bottle_types,
                           is_my_list=is_my_list)


@main_blueprint.route("/<username>/<bottle_id>")
def bottle_detail(username: str, bottle_id: str):
    user = User.query.filter(User.username == username).first_or_404()
    _bottle = Bottle.query.get_or_404(bottle_id)
    return render_template("bottle_detail.html", user=user, bottle=_bottle)


@main_blueprint.route("/terms")
def terms():
    return render_template("tos.html")


@main_blueprint.route("/privacy")
def privacy():
    return render_template("tos_privacy.html")


@main_blueprint.route("/cookies")
def cookies():
    return render_template("tos_cookies.html")
