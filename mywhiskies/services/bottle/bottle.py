import random

import boto3
from flask import flash, make_response, render_template, request
from flask.wrappers import Response

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils
from mywhiskies.services.bottle.image import (
    add_bottle_images,
    delete_bottle_images,
    edit_bottle_images,
    get_bottle_image_count,
    get_s3_config,
)


def list_bottles(user: User, request: request, current_user: User) -> Response:
    all_bottles = user.bottles
    killed_bottles = [b for b in all_bottles if b.date_killed]

    if request.method == "POST":
        active_bottle_types = request.form.getlist("bottle_type")

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

    page_title = f"{user.username}'{'' if user.username.endswith('s') else 's'} Whiskies: Bottles"

    response = make_response(
        render_template(
            "bottle/bottle_list.html",
            title=page_title,
            has_datatable=True,
            user=user,
            bottles=bottles_to_list,
            has_killed_bottles=bool(len(killed_bottles)),
            bottle_types=BottleTypes,
            active_filters=active_bottle_types,
            dt_list_length=request.cookies.get("dt-list-length", "50"),
            is_my_list=utils.is_my_list(user.username, current_user),
        )
    )

    return response


def add_bottle(form: BottleAddForm, user: User) -> None:
    distilleries = []
    for distillery_id in form.distilleries.data:
        distilleries.append(db.session.get(Distillery, distillery_id))

    bottler_id = form.bottler_id.data if form.bottler_id.data != "0" else None

    bottle_in = Bottle(
        user_id=user.id,
        name=form.name.data,
        url=form.url.data,
        type=form.type.data,
        distilleries=distilleries,
        bottler_id=bottler_id,
        size=form.size.data,
        year_barrelled=form.year_barrelled.data,
        year_bottled=form.year_bottled.data,
        abv=form.abv.data,
        description=form.description.data,
        review=form.review.data,
        stars=form.stars.data,
        cost=form.cost.data,
        date_purchased=form.date_purchased.data,
        date_opened=form.date_opened.data,
        date_killed=form.date_killed.data,
    )

    db.session.add(bottle_in)
    db.session.commit()

    db.session.flush()
    flash_message = f'"{bottle_in.name}" has been successfully added.'
    flash_category = "success"

    image_upload_success = add_bottle_images(form, bottle_in)

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


def edit_bottle(form: BottleEditForm, bottle: Bottle) -> None:
    distilleries = []
    for distillery_id in form.distilleries.data:
        distilleries.append(db.session.get(Distillery, distillery_id))

    bottler_id = form.bottler_id.data if form.bottler_id.data != "0" else None

    bottle.name = form.name.data
    bottle.url = form.url.data
    bottle.type = form.type.data
    bottle.distilleries = distilleries
    bottle.bottler_id = bottler_id
    bottle.size = form.size.data
    bottle.year_barrelled = form.year_barrelled.data
    bottle.year_bottled = form.year_bottled.data
    bottle.abv = form.abv.data
    bottle.description = form.description.data
    bottle.review = form.review.data
    bottle.stars = form.stars.data
    bottle.cost = form.cost.data
    bottle.date_purchased = form.date_purchased.data
    bottle.date_opened = form.date_opened.data
    bottle.date_killed = form.date_killed.data

    edit_bottle_images(form, bottle)
    image_upload_success = add_bottle_images(form, bottle)

    if image_upload_success:
        delete_bottle_images(bottle)
        flash_message = f'"{bottle.name}" has been successfully updated.'
        flash_category = "success"
        bottle.image_count = get_bottle_image_count(bottle.id)
        db.session.add(bottle)
        db.session.commit()
    else:
        flash_message = f'An error occurred while updating "{bottle.name}".'
        flash_category = "danger"

    flash(flash_message, flash_category)


def delete_bottle(user: User, bottle_id: str) -> None:
    user_bottles = [b.id for b in user.bottles]
    if bottle_id not in user_bottles:
        flash("There was an issue deleting the bottle.", "danger")
        return
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    bottle_to_delete = db.get_or_404(Bottle, bottle_id)
    db.session.delete(bottle_to_delete)

    if bottle_to_delete.image_count:
        s3_client = boto3.client("s3")
        for i in range(1, bottle_to_delete.image_count + 1):
            s3_client.delete_object(
                Bucket=f"{img_s3_bucket}",
                Key=f"{img_s3_key}/{bottle_to_delete.id}_{i}.png",
            )
    db.session.commit()
    flash("Bottle deleted succesfully", "success")
