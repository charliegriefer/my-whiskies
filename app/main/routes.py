from flask import flash, redirect, render_template, request
from flask_login import current_user, login_required
import io
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from app.extensions import db
from app.main import main_blueprint
from app.main.forms import BottleForm, DistilleryForm
from app.models import User
from app.models.bottle import Bottle, BottleTypes, Distillery
from sqlalchemy import insert


@main_blueprint.route("/")
@main_blueprint.route("/index")
def index():
    return render_template("index.html", title="Home")


@main_blueprint.route("/home")
@login_required
def home():
    bottles = Bottle.query.filter(Bottle.user_id == current_user.id).all()
    distilleries = Distillery.query.filter(Distillery.user_id == current_user.id).all()
    return render_template("home.html", user=current_user, bottles=bottles, distilleries=distilleries)


@main_blueprint.route("/add_distilleries")
@login_required
def add_distilleries():
    if request.referrer.split("/")[-1] != "home":
        return redirect("home")

    distilleries = [d.__dict__ for d in Distillery.query.filter(Distillery.user_id == 0).all()]
    for _distillery in distilleries:
        del _distillery["id"]
        del _distillery["_sa_instance_state"]
        _distillery["user_id"] = current_user.id

    db.session.execute(insert(Distillery), distilleries)
    db.session.commit()
    
    flash(f"{len(distilleries)} have been added to your account.")
    return redirect("home")


@main_blueprint.route("/distillery", methods=["GET", "POST"])
@login_required
def distillery():
    form = DistilleryForm()
    if request.method == "POST" and form.validate_on_submit():
        distillery_in = Distillery(name=form.name.data,
                                   description=form.description.data,
                                   region_1=form.region_1.data,
                                   region_2=form.region_2.data,
                                   url=form.url.data,
                                   user_id=current_user.id)
        db.session.add(distillery_in)
        db.session.commit()
        flash(f"\"{distillery_in.name}\" has been successfully added.", "success")
        return redirect("home")
    return render_template("distillery_add.html", form=form)


@main_blueprint.route("/bottle", methods=["GET", "POST"])
@login_required
def bottle():
    form = BottleForm()

    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    form.distillery.choices = [(x.id, x.name) for x in Distillery.query.all()]
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
        bottle_in = Bottle(name=form.name.data,
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
            bottle_in.url = form.url.data
        if form.description.data and form.description.data != "":
            bottle_in.description = form.description.data
        if form.review.data and form.review.data != "":
            bottle_in.review = form.review.data

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
            ext = image_in.format.lower()

            if image_in.width > 300:
                # calculate new height and width
                divisor = image_in.width/300
                image_dims = (int(image_in.width/divisor), int(image_in.height/divisor))
                image_in = image_in.resize(image_dims)

            new_filename = f"{bottle_in.id}.{ext}"

            in_mem_file = io.BytesIO()
            image_in.save(in_mem_file, format=ext)
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


@main_blueprint.route("/<username>")
def bottle_list(username: str):
    user = User.query.filter(User.username == username).first_or_404()
    bottles = Bottle.query.filter(Bottle.user_id == user.id).all()
    return render_template("bottle_list.html", user=user, bottles=bottles)


@main_blueprint.route("/<username>/<bottle_id>")
def bottle_detail(username: str, bottle_id: str):
    user = User.query.filter(User.username == username).first_or_404()
    _bottle = Bottle.query.get_or_404(bottle_id)
    return render_template("bottle_detail.html", user=user, bottle=_bottle)
