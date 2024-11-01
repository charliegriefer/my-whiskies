import random

import boto3
from flask import flash
from flask_login import current_user

from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.extensions import db
from mywhiskies.services.bottle.image import (
    add_bottle_images,
    delete_bottle_images,
    edit_bottle_images,
    get_bottle_image_count,
    get_s3_config,
)


def list_bottles(user, request):
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

    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == user.username.lower()
    )

    return bottles_to_list, active_bottle_types, is_my_list, killed_bottles


def add_bottle(form, user) -> None:
    distilleries = []
    for distillery_id in form.distilleries.data:
        distilleries.append(db.session.get(Distillery, distillery_id))

    bottler_id = form.bottler_id.data if form.bottler_id.data != "0" else None

    bottle = Bottle(
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

    db.session.add(bottle)
    db.session.commit()

    db.session.flush()
    flash_message = f'"{bottle.name}" has been successfully added.'
    flash_category = "success"

    image_upload_success = add_bottle_images(form, bottle)

    if image_upload_success:
        pass
    else:
        flash_message = f'An error occurred while creating "{bottle.name}".'
        flash_category = "danger"
        db.session.delete(bottle)
        db.session.commit()

    bottle.image_count = get_bottle_image_count(bottle.id)
    db.session.commit()

    flash(flash_message, flash_category)


def edit_bottle(form, bottle):
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


def delete_bottle(bottle_id: str) -> None:
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
