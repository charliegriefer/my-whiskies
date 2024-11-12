import io
from typing import Union

import boto3
from botocore.exceptions import ClientError
from flask import current_app
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle


def get_s3_config():
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        current_app.config["BOTTLE_IMAGE_S3_URL"]
        + "/"
        + current_app.config["BOTTLE_IMAGE_S3_KEY"],
    )


def get_bottle_image_count(bottle_id: str) -> int:
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    images = s3_client.list_objects(
        Bucket=f"{img_s3_bucket}", Prefix=f"{img_s3_key}/{bottle_id}"
    ).get("Contents", [])
    return len(images)


def add_bottle_images(
    form: Union[BottleAddForm, BottleEditForm], bottle_in: Bottle
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


def edit_bottle_images(form: BottleEditForm, bottle: Bottle):
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


def delete_bottle_images(bottle: Bottle):
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    for i in range(1, 4):
        s3_client.delete_object(
            Bucket=f"{img_s3_bucket}", Key=f"{img_s3_key}/__del_{bottle.id}_{i}.png"
        )
