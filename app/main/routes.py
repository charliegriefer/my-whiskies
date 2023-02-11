from flask import redirect, render_template, request
from flask_login import current_user, login_required

import boto3
from botocore.exceptions import ClientError

from app.extensions import db
from app.main import main_blueprint
from app.main.forms import BottleForm, DistilleryForm
from app.models import User
from app.models.bottle import Bottle, BottleTypes, Distillery


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
        return redirect("home")
    return render_template("add_distillery.html", form=form)


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
        if form.notes.data and form.notes.data != "":
            bottle_in.notes = form.notes.data
        if form.review.data and form.review.data != "":
            bottle_in.review = form.review.data

        if form.date_purchased.data and form.date_purchased.data != "":
            bottle_in.date_purchased = form.date_purchased.data
        if form.date_killed.data and form.date_killed.data != "":
            bottle_in.date_killed = form.date_killed.data

        db.session.add(bottle_in)
        db.session.commit()
        db.session.flush()

        if form.image.data:
            q = form.image.data
            new_filename = f"{bottle_in.id}.{q.filename.split('.')[-1]}"
            s3_client = boto3.client("s3")

            try:
                s3_client.put_object(Body=q, Bucket="my-whiskies", Key=f"bottle-pics/{new_filename}")
            except ClientError:
                pass

        return redirect("home")

    return render_template("add_bottle.html", form=form)


@main_blueprint.route("/<username>")
def bottle_list(username: str):
    user = User.query.filter(User.username == username).first_or_404()
    bottles = Bottle.query.filter(Bottle.user_id == user.id).all()
    return render_template("bottle_list.html", user=user, bottles=bottles)


@main_blueprint.route("/<username>/<bottle_id>")
def bottle_detail(username: str, bottle_id: str):
    user = User.query.filter(User.username == username).first_or_404()
    bottle = Bottle.query.get_or_404(bottle_id)
    return render_template("bottle_detail.html", user=user, bottle=bottle)
