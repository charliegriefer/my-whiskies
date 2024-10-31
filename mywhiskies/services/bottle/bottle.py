import io

# import random
# rom datetime import datetime
from typing import Union

import boto3
from botocore.exceptions import ClientError
from flask import current_app, flash
from flask_login import current_user
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleEditForm, BottleForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.extensions import db


def get_s3_config():
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        current_app.config["BOTTLE_IMAGE_S3_URL"]
        + "/"
        + current_app.config["BOTTLE_IMAGE_S3_KEY"],
    )


def prepare_bottle_form(
    user, form: Union[BottleForm, BottleEditForm]
) -> Union[BottleForm, BottleEditForm]:
    # set up bottle type dropdown
    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.sort()
    form.type.choices.append(
        form.type.choices.pop(form.type.choices.index(("other", "Other")))
    )
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    # set up distilleries dropdown
    distilleries = user.distilleries
    distilleries.sort(key=lambda d: d.name)
    form.distilleries.choices = [(d.id, d.name) for d in distilleries]
    form.distilleries.choices.insert(0, ("", "Choose One or More Distilleries"))
    form.distilleries.choices.insert(1, ("", " "))

    # set up bottlers dropdown
    bottlers = user.bottlers
    bottlers.sort(key=lambda d: d.name)
    form.bottler_id.choices = [(b.id, b.name) for b in bottlers]
    form.bottler_id.choices.insert(0, (0, "Distillery Bottling"))

    # set up star rating dropdown
    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    return form


def add_bottle(form, user) -> Bottle:
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

    image_upload_success = bottle_add_images(form, bottle)

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
    return bottle


def handle_bottle_edit(form, bottle):
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

    bottle_edit_images(form, bottle)
    image_upload_success = bottle_add_images(form, bottle)

    if image_upload_success:
        bottle_delete_images(bottle)
        flash_message = f'"{bottle.name}" has been successfully updated.'
        flash_category = "success"
        bottle.image_count = get_bottle_image_count(bottle.id)
        db.session.add(bottle)
        db.session.commit()
    else:
        flash_message = f'An error occurred while updating "{bottle.name}".'
        flash_category = "danger"

    flash(flash_message, flash_category)


def list_user_bottles(user, request):
    all_bottles = user.bottles
    killed_bottles = [b for b in all_bottles if b.date_killed]

    active_bottle_types = (
        request.form.getlist("bottle_type")
        if request.method == "POST"
        else [bt.name for bt in BottleTypes]
    )

    if request.method == "POST":
        bottles_to_list = (
            [b for b in all_bottles if b.type.name in active_bottle_types]
            if active_bottle_types
            else []
        )
    else:
        bottles_to_list = all_bottles

    is_my_list = (
        current_user.is_authenticated
        and current_user.username.lower() == user.username.lower()
    )

    return bottles_to_list, active_bottle_types, is_my_list, killed_bottles


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
            img_s3_bucket, img_s3_key, _ = get_s3_config()
            try:
                s3_client.put_object(
                    Body=in_mem_file,
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{new_filename}.png",
                    ContentType="image/png",
                )
            except ClientError:
                # TODO: log error
                return False

    return True


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


def get_bottle_image_count(bottle_id: str) -> int:
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    images = s3_client.list_objects(
        Bucket=f"{img_s3_bucket}", Prefix=f"{img_s3_key}/{bottle_id}"
    ).get("Contents", [])
    return len(images)


def bottle_edit_images(form: BottleEditForm, bottle: Bottle):
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    for i in range(1, 4):
        if form[f"remove_image_{i}"].data:
            s3_client.copy_object(
                Bucket=f"{img_s3_bucket}",
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{i}.png",
                Key=f"__del_{bottle.id}_{i}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket=f"{img_s3_bucket}", Key=f"{img_s3_key}/{bottle.id}_{i}.png"
            )

    images = s3_client.list_objects(
        Bucket=f"{img_s3_bucket}", Prefix=f"{img_s3_key}/{bottle.id}"
    ).get("Contents", [])
    images.sort(key=lambda obj: obj.get("Key"))

    for idx, img in enumerate(images, 1):
        img_num = int(img.get("Key").split("_")[-1].split(".")[0])

        if idx != img_num:
            s3_client.copy_object(
                Bucket=f"{img_s3_bucket}",
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{img_num}.png",
                Key=f"{img_s3_key}/{bottle.id}_{idx}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket=f"{img_s3_bucket}", Key=f"{img_s3_key}/{bottle.id}_{img_num}.png"
            )


def bottle_delete_images(bottle: Bottle):
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    for i in range(1, 4):
        s3_client.delete_object(
            Bucket=f"{img_s3_bucket}", Key=f"{img_s3_key}/__del_{bottle.id}_{i}.png"
        )
