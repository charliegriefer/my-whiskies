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
    get_s3_config,
)


def list_bottles_by_user(user: User, request: request, current_user: User) -> Response:
    return utils.prep_datatable_bottles(user, current_user, request)


def add_bottle(form: BottleAddForm, user: User) -> Bottle:
    """Creates a new bottle record and uploads images if provided."""
    distilleries = [
        db.session.get(Distillery, distillery_id)
        for distillery_id in form.distilleries.data
    ]

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
        is_private=form.is_private.data,
        personal_note=form.personal_note.data,
    )

    db.session.add(bottle)
    db.session.commit()

    # Upload images
    if add_bottle_images(form, bottle):
        flash(f'"{bottle.name}" has been successfully added.', "success")
    else:
        db.session.delete(bottle)
        db.session.commit()
        flash(f'An error occurred while creating "{bottle.name}".', "danger")
        return None  # Bottle creation failed

    current_app.logger.info(f"{user.username} added bottle {bottle.name} successfully.")
    return bottle


def edit_bottle(form: BottleEditForm, bottle: Bottle) -> None:
    """Updates a bottle's details and manages its images properly."""

    # Update bottle details
    distilleries = [
        db.session.get(Distillery, distillery_id)
        for distillery_id in form.distilleries.data
    ]
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

    db.session.add(bottle)
    db.session.commit()

    # Handle image updates for individual fields
    images = [
        form.bottle_image_1.data,
        form.bottle_image_2.data,
        form.bottle_image_3.data,
    ]

    for idx, image in enumerate(images, start=1):
        if image:
            # Remove the old image for this sequence (if it exists)
            existing_image = next(
                (img for img in bottle.images if img.sequence == idx), None
            )
            if existing_image:
                delete_bottle_images(bottle, [existing_image.id])  # Delete old image
                db.session.delete(existing_image)

            # Add the new image
            add_bottle_images(form, bottle, idx=idx)

    # Reorder image sequences to avoid duplication
    images = sorted(bottle.images, key=lambda img: img.sequence)
    for idx, img in enumerate(images, start=1):
        img.sequence = idx  # Reorder to avoid gaps

    db.session.commit()

    flash(f'"{bottle.name}" has been successfully updated.', "success")
    current_app.logger.info(
        f"{bottle.user.username} edited bottle {bottle.name} successfully."
    )


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
