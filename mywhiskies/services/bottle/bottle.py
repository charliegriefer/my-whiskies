import boto3
from flask import current_app, flash, request
from flask.wrappers import Response

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle
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


def list_bottles_by_user(user: User, request: request, current_user: User) -> Response:
    return utils.prep_datatable_bottles(user, current_user, request)


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
        is_private=form.is_private.data,
        personal_note=form.personal_note.data,
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

    current_app.logger.info(
        f"{user.username} added bottle {form.name.data} successfully."
    )
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
    bottle.is_private = form.is_private.data
    bottle.personal_note = form.personal_note.data
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

    current_app.logger.info(
        f"{bottle.user.username} edited bottle {bottle.name} successfully."
    )
    flash(flash_message, flash_category)


def delete_bottle(user: User, bottle_id: str) -> None:
    bottle = db.get_or_404(Bottle, bottle_id)
    if bottle.user_id != user.id:
        flash("There was an issue deleting this bottle.", "danger")
        return

    img_s3_bucket, img_s3_key, _ = get_s3_config()

    if bottle.image_count:
        s3_client = boto3.client("s3")
        for i in range(1, bottle.image_count + 1):
            s3_client.delete_object(
                Bucket=f"{img_s3_bucket}",
                Key=f"{img_s3_key}/{bottle.id}_{i}.png",
            )

    db.session.delete(bottle)
    db.session.commit()
    current_app.logger.info(
        f"{user.username} deleted bottle {bottle.name} successfully."
    )
    flash("Bottle deleted successfully", "success")
