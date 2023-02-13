import io

import boto3
from PIL import Image
from botocore.exceptions import ClientError
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import insert
from sqlalchemy.sql.expression import func

from app.extensions import db
from app.main import main_blueprint
from app.main.forms import BottleForm, DistilleryForm
from app.models import User
from app.models.bottle import Bottle, BottleTypes, Distillery


@main_blueprint.route("/")
@main_blueprint.route("/home")
def home():
    if current_user.is_authenticated:
        my_bottles = Bottle.query.filter(Bottle.user_id == current_user.id).all()
        my_distilleries = Distillery.query.filter(Distillery.user_id == current_user.id).all()
        return render_template("home.html",
                               title=f"{current_user.username}'s Whiskies| Home Page",
                               user=current_user,
                               bottles=my_bottles,
                               distilleries=my_distilleries)
    else:
        return render_template("index.html", title="Home")


@main_blueprint.route("/add_distilleries")
@login_required
def add_distilleries():
    if request.referrer.split("/")[-1] != "home":
        return redirect("home")

    if Distillery.query.filter(Distillery.user_id == current_user.id).count() > 0:
        return redirect("home")

    base_distilleries = [d.__dict__ for d in Distillery.query.filter(Distillery.user_id == 0).all()]
    for _distillery in base_distilleries:
        del _distillery["id"]
        del _distillery["_sa_instance_state"]
        _distillery["user_id"] = current_user.id

    db.session.execute(insert(Distillery), base_distilleries)
    db.session.commit()

    flash(f"{len(base_distilleries)} distilleries have been added to your account.")
    return redirect("home")


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
        return redirect("home")
    return render_template("distillery_add.html",
                           title=f"{current_user.username}'s Whiskies | Add Distillery",
                           user=current_user,
                           form=form)


@main_blueprint.route("/bottle_delete/<string:bottle_id>")
@login_required
def bottle_delete(bottle_id: str):
    bottle_to_delete = Bottle.query.get_or_404(bottle_id)

    db.session.delete(bottle_to_delete)

    s3_client = boto3.client("s3")
    s3_client.delete_object(Bucket="my-whiskies", Key=f"bottle-pics/{bottle_to_delete.id}.png")
    db.session.commit()

    flash(f"\"{bottle_to_delete.name}\" has been successfully deleted.", "success")
    return redirect(url_for("main.list_bottles", username=current_user.username))


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

    distilleries = Distillery.query.filter_by(user_id=current_user.id).order_by("name").all()
    form.distillery.choices = [(x.id, x.name) for x in distilleries]
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
        bottle_in = Bottle(name=form.name.data.strip(),
                           type=form.type.data,
                           abv=form.abv.data,
                           cost=form.cost.data,
                           distillery_id=form.distillery.data,
                           user_id=current_user.id)

        if form.year.data and form.year.data != "":
            bottle_in.year = form.year.data.strip()
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

        if form.bottle_image.data:
            image_in = Image.open(form.bottle_image.data)

            if image_in.width > 300:
                # calculate new height and width
                divisor = image_in.width/300
                image_dims = (int(image_in.width/divisor), int(image_in.height/divisor))
                image_in = image_in.resize(image_dims)

            new_filename = f"{bottle_in.id}.png"

            in_mem_file = io.BytesIO()
            image_in.save(in_mem_file, format="png")
            in_mem_file.seek(0)

            s3_client = boto3.client("s3")
            try:
                s3_client.put_object(Body=in_mem_file, Bucket="my-whiskies", Key=f"bottle-pics/{new_filename}")
                bottle_in.has_image = True
                db.session.commit()
            except ClientError:
                flash_message = f"An error occurred while creating \"{bottle_in.name}\"."
                flash_category = "danger"
                Bottle.query.filter_by(id=bottle_in.id).delete()
                db.session.commit()

        flash(flash_message, flash_category)
        return redirect("home")

    return render_template("bottle_add.html", form=form)


@main_blueprint.route("/<username>", methods=["GET", "POST"], endpoint="list_bottles")
def bottle_list(username: str):
    user = User.query.filter(User.username == username).first_or_404()
    bottles = Bottle.query.filter(Bottle.user_id == user.id)
    bottle_types = []

    if request.method == "POST":
        bottle_types = request.form.getlist("bottle_type")
        if len(bottle_types):
            bottles = bottles.filter(Bottle.type.in_(bottle_types))
        if request.form.get("random_toggle"):
            bottles = bottles.order_by(func.random())

    if request.form.get("random_toggle"):
        bottles = bottles.first()
        if bottles:
            bottles = [bottles]
        else:
            bottles = []
    else:
        bottles = bottles.all()

    return render_template("bottle_list.html",
                           title=f"{user.username}'s Whiskies| Bottles",
                           user=user,
                           bottles=bottles,
                           selected_length=request.form.get("bottle_length", 50),
                           bottle_types=BottleTypes,
                           active_filters=bottle_types)


@main_blueprint.route("/<username>/<bottle_id>")
def bottle_detail(username: str, bottle_id: str):
    user = User.query.filter(User.username == username).first_or_404()
    _bottle = Bottle.query.get_or_404(bottle_id)
    return render_template("bottle_detail.html", user=user, bottle=_bottle)
