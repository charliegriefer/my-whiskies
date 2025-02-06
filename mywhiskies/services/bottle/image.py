import io

import boto3
from botocore.exceptions import ClientError
from flask import current_app
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleImage
from mywhiskies.extensions import db


def get_s3_config():
    """Retrieve S3 bucket configuration from Flask config."""
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        f"{current_app.config['BOTTLE_IMAGE_S3_URL']}/{current_app.config['BOTTLE_IMAGE_S3_KEY']}",
    )


def get_bottle_image_count(bottle_id: str) -> int:
    """Returns the number of images stored in S3 for a given bottle."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    images = s3_client.list_objects(
        Bucket=img_s3_bucket, Prefix=f"{img_s3_key}/{bottle_id}"
    ).get("Contents", [])
    return len(images)


def add_bottle_images(form: BottleAddForm, bottle: Bottle) -> bool:
    """Processes image uploads and stores metadata in the database."""
    uploaded_images = []

    for i in range(1, 4):
        image_field = form[f"bottle_image_{i}"]
        if image_field.data:
            uploaded_images.append((i, image_field.data))

    if not uploaded_images:
        return True  # No images to process

    uploaded_images.sort()  # Sort by field order
    new_sequence = 1  # Start numbering from 1

    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    for _, image_data in uploaded_images:
        try:
            image_in = Image.open(image_data)

            # Resize image if necessary
            if image_in.width > 400:
                ratio = 400 / image_in.width
                new_size = (400, int(image_in.height * ratio))
                image_in = image_in.resize(new_size)

            # Generate new filename
            new_filename = f"{bottle.id}_{new_sequence}.png"

            # Save to S3
            in_mem_file = io.BytesIO()
            image_in.save(in_mem_file, format="PNG")
            in_mem_file.seek(0)

            s3_client.put_object(
                Body=in_mem_file,
                Bucket=img_s3_bucket,
                Key=f"{img_s3_key}/{new_filename}",
                ContentType="image/png",
            )

            # Add record to bottle_image table
            db.session.add(BottleImage(bottle_id=bottle.id, sequence=new_sequence))
            new_sequence += 1

        except ClientError:
            return False  # Image upload failed

    db.session.commit()
    return True


def edit_bottle_images(form: BottleEditForm, bottle: Bottle) -> None:
    """Handles image modifications and renumbering for edited bottles."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    # Handle image deletions
    for i in range(1, 4):
        if form[f"remove_image_{i}"].data:
            s3_client.delete_object(
                Bucket=img_s3_bucket, Key=f"{img_s3_key}/{bottle.id}_{i}.png"
            )

    # Fetch remaining images and renumber them
    images = s3_client.list_objects(
        Bucket=img_s3_bucket, Prefix=f"{img_s3_key}/{bottle.id}"
    ).get("Contents", [])

    images.sort(key=lambda obj: obj["Key"])  # Ensure order
    for idx, img in enumerate(images, 1):
        img_num = int(img["Key"].split("_")[-1].split(".")[0])

        if idx != img_num:  # If numbering is incorrect, rename
            s3_client.copy_object(
                Bucket=img_s3_bucket,
                CopySource=f"{img_s3_bucket}/{img['Key']}",
                Key=f"{img_s3_key}/{bottle.id}_{idx}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(Bucket=img_s3_bucket, Key=img["Key"])


def delete_bottle_images(bottle: Bottle) -> None:
    """Deletes all images for a given bottle."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    for i in range(1, 4):
        s3_client.delete_object(
            Bucket=img_s3_bucket, Key=f"{img_s3_key}/{bottle.id}_{i}.png"
        )
