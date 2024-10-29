import io
import random
import time
from datetime import datetime
from typing import Union

import boto3
from botocore.exceptions import ClientError
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
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleEditForm, BottleForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

bottle = Blueprint("bottle", __name__, template_folder="templates")


@bottle.route(
    "/<username>/bottles",
    methods=["GET", "POST"],
    endpoint="list_bottles",
    strict_slashes=False,
)
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
    user = db.one_or_404(db.select(User).filter_by(username=username))

    all_bottles = user.bottles
    killed_bottles = [b for b in all_bottles if b.date_killed]

    if request.method == "POST":
        active_bottle_types = request.form.getlist(
            "bottle_type"
        )  # checked bottle types to show

        if len(active_bottle_types):
            bottles_to_list = [
                b for b in all_bottles if b.type.name in active_bottle_types
            ]
            if bool(int(request.form.get("random_toggle"))):
                if len(bottles_to_list) > 0:
                    unkilled_bottles = [b for b in bottles_to_list if not b.date_killed]
                    bottles_to_list = [random.choice(unkilled_bottles)]
        else:
            bottles_to_list = []

    else:
        active_bottle_types = [bt.name for bt in BottleTypes]
        bottles_to_list = all_bottles

    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )

    response = make_response(
        render_template(
            "bottle/bottle_list.html",
            title=f"{user.username}'s Whiskies: Bottles",
            has_datatable=True,
            user=user,
            bottles=bottles_to_list,
            has_killed_bottles=bool(len(killed_bottles)),
            bottle_types=BottleTypes,
            active_filters=active_bottle_types,
            dt_list_length=dt_list_length,
            is_my_list=is_my_list,
        )
    )

    response.set_cookie(
        "dt-list-length",
        value=dt_list_length,
        expires=datetime.now() + relativedelta(years=1),
    )
    return response


@bottle.route("/bottle/<bottle_id>")
def bottle_detail(bottle_id: str):
    _bottle = db.get_or_404(Bottle, bottle_id)
    is_my_bottle = current_user.is_authenticated and _bottle.user_id == current_user.id

    return render_template(
        "bottle/bottle_detail.html",
        title=f"{_bottle.user.username}'s Whiskies: {_bottle.name}",
        bottle=_bottle,
        user=_bottle.user,
        ts=time.time(),
        is_my_bottle=is_my_bottle,
    )


@bottle.route("/bottle/add", methods=["GET", "POST"])
@login_required
def bottle_add():
    form = prep_bottle_form(current_user, BottleForm())

    if request.method == "POST" and form.validate_on_submit():
        bottle_in = Bottle(user_id=current_user.id)

        bottle_in.name = form.name.data
        bottle_in.url = form.url.data
        bottle_in.type = form.type.data
        d = []
        for distllery_id in form.distilleries.data:
            d.append(Distillery.query.get(distllery_id))
        bottle_in.distilleries = d
        bottle_in.bottler_id = form.bottler_id.data
        bottle_in.size = form.size.data
        bottle_in.year_barrelled = form.year_barrelled.data
        bottle_in.year_bottled = form.year_bottled.data
        bottle_in.abv = form.abv.data
        bottle_in.description = form.description.data
        bottle_in.review = form.review.data
        bottle_in.stars = form.stars.data
        bottle_in.cost = form.cost.data
        bottle_in.date_purchased = form.date_purchased.data
        bottle_in.date_opened = form.date_opened.data
        bottle_in.date_killed = form.date_killed.data

        # handle "Distillery Bottling"
        if bottle_in.bottler_id == "0":
            bottle_in.bottler_id = None

        db.session.add(bottle_in)
        db.session.commit()

        db.session.flush()  # to get the id of the newly created bottle
        flash_message = f'"{bottle_in.name}" has been successfully added.'
        flash_category = "success"

        image_upload_success = bottle_add_images(form, bottle_in)

        if image_upload_success:
            pass
        else:
            flash_message = f'An error occurred while creating "{bottle_in.name}".'
            flash_category = "danger"
            db.session.delete(bottle_in)
            db.session.commit()

        bottle_in.image_count = get_bottle_image_count(bottle_in.id)

        db.session.commit()

        flash(flash_message, flash_category)
        return redirect(url_for("core.home", username=current_user.username.lower()))

    return render_template(
        "bottle/bottle_add.html",
        title=f"{current_user.username}'s Whiskies: Add Bottle",
        form=form,
    )


@bottle.route("/bottle/edit/<string:bottle_id>", methods=["GET", "POST"])
@login_required
def bottle_edit(bottle_id: str):
    _bottle = db.get_or_404(Bottle, bottle_id)
    form = prep_bottle_form(current_user, BottleEditForm(obj=_bottle))

    if request.method == "POST" and form.validate_on_submit():
        _bottle.name = form.name.data
        _bottle.url = form.url.data
        _bottle.type = form.type.data
        d = []
        for distllery_id in form.distilleries.data:
            d.append(Distillery.query.get(distllery_id))
        _bottle.distilleries = d
        _bottle.bottler_id = form.bottler_id.data
        _bottle.size = form.size.data
        _bottle.year_barrelled = form.year_barrelled.data
        _bottle.year_bottled = form.year_bottled.data
        _bottle.abv = form.abv.data
        _bottle.description = form.description.data
        _bottle.review = form.review.data
        _bottle.stars = form.stars.data
        _bottle.cost = form.cost.data
        _bottle.date_purchased = form.date_purchased.data
        _bottle.date_opened = form.date_opened.data
        _bottle.date_killed = form.date_killed.data

        # handle "Distillery Bottling"
        if _bottle.bottler_id == "0":
            _bottle.bottler_id = None

        bottle_edit_images(form, _bottle)
        image_upload_success = bottle_add_images(form, _bottle)

        if image_upload_success:
            bottle_delete_images(_bottle)
            flash_message = f'"{_bottle.name}" has been successfully updated.'
            flash_category = "success"
            _bottle.image_count = get_bottle_image_count(_bottle.id)
            db.session.add(_bottle)
            db.session.commit()
        else:
            flash_message = f'An error occurred while updating "{_bottle.name}".'
            flash_category = "danger"

        flash(flash_message, flash_category)
        return redirect(url_for("core.home", username=current_user.username.lower()))

    else:
        form.type.data = _bottle.type.name
        form.distilleries.data = [d.id for d in _bottle.distilleries]
        return render_template(
            "bottle/bottle_edit.html",
            title=f"{current_user.username}'s Whiskies: Edit Bottle",
            ts=time.time(),
            bottle=_bottle,
            form=form,
        )


@bottle.route("/bottle/delete/<string:bottle_id>")
@login_required
def bottle_delete(bottle_id: str):
    bottle_to_delete = db.get_or_404(Bottle, bottle_id)
    db.session.delete(bottle_to_delete)

    if bottle_to_delete.image_count:
        s3_client = boto3.client("s3")
        for i in range(1, bottle_to_delete.image_count + 1):
            s3_client.delete_object(
                Bucket="my-whiskies-pics", Key=f"{bottle_to_delete.id}_{i}.png"
            )
    db.session.commit()

    flash(f'"{bottle_to_delete.name}" has been successfully deleted.', "success")
    return redirect(
        url_for("bottle.list_bottles", username=current_user.username.lower())
    )


def prep_bottle_form(
    user, form: Union[BottleForm, BottleEditForm]
) -> Union[BottleForm, BottleEditForm]:
    # set up the bottle types dropdown
    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    # sort the list and move "Other" to the bottom
    form.type.choices.sort()
    form.type.choices.append(
        form.type.choices.pop(form.type.choices.index(("other", "Other")))
    )
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    # set up the distilleries dropdown
    distilleries = user.distilleries
    distilleries.sort(key=lambda d: d.name)
    form.distilleries.choices = [(d.id, d.name) for d in distilleries]
    form.distilleries.choices.insert(0, ("", "Choose One or More Distilleries"))
    form.distilleries.choices.insert(1, ("", " "))

    # set up the bottlers dropdown
    bottlers = user.bottlers
    bottlers.sort(key=lambda d: d.name)
    form.bottler_id.choices = [(b.id, b.name) for b in bottlers]
    form.bottler_id.choices.insert(0, (0, "Distillery Bottling"))

    # set up the star rating dropdown
    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    return form


def bottle_add_images(
    form: Union[BottleForm, BottleEditForm], bottle_in: Bottle
) -> bool:
    for i in range(1, 4):
        image_field = form[f"bottle_image_{i}"]

        if image_field.data:
            image_in = Image.open(image_field.data)
            if image_in.width > 400:
                divisor = image_in.width / 400
                image_dims = (
                    int(image_in.width / divisor),
                    int(image_in.height / divisor),
                )
                image_in = image_in.resize(image_dims)

            new_filename = f"{bottle_in.id}_{i}"

            in_mem_file = io.BytesIO()
            image_in.save(in_mem_file, format="png")
            in_mem_file.seek(0)

            s3_client = boto3.client("s3")
            try:
                s3_client.put_object(
                    Body=in_mem_file,
                    Bucket="my-whiskies-pics",
                    Key=f"{new_filename}.png",
                    ContentType="image/png",
                )
            except ClientError:
                # TODO: log error
                return False

    return True


def bottle_edit_images(form: BottleEditForm, bottle: Bottle):
    s3_client = boto3.client("s3")

    for i in range(1, 4):
        if form[f"remove_image_{i}"].data:
            s3_client.copy_object(
                Bucket="my-whiskies-pics",
                CopySource=f"my-whiskies-pics/{bottle.id}_{i}.png",
                Key=f"__del_{bottle.id}_{i}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket="my-whiskies-pics", Key=f"{bottle.id}_{i}.png"
            )

    images = s3_client.list_objects(Bucket="my-whiskies-pics", Prefix=bottle.id).get(
        "Contents", []
    )
    images.sort(key=lambda obj: obj.get("Key"))

    for idx, img in enumerate(images, 1):
        img_num = int(img.get("Key").split("_")[-1].split(".")[0])

        if idx != img_num:
            s3_client.copy_object(
                Bucket="my-whiskies-pics",
                CopySource=f"my-whiskies-pics/{bottle.id}_{img_num}.png",
                Key=f"{bottle.id}_{idx}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket="my-whiskies-pics", Key=f"{bottle.id}_{img_num}.png"
            )


def bottle_delete_images(bottle: Bottle):
    s3_client = boto3.client("s3")
    for i in range(1, 4):
        s3_client.delete_object(
            Bucket="my-whiskies-pics", Key=f"__del_{bottle.id}_{i}.png"
        )


def get_bottle_image_count(bottle_id: str) -> int:
    s3_client = boto3.client("s3")
    images = s3_client.list_objects(Bucket="my-whiskies-pics", Prefix=bottle_id).get(
        "Contents", []
    )
    return len(images)
