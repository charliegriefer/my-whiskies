import io

import boto3
from botocore.exceptions import ClientError
from flask import current_app
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleAddForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleImage
from mywhiskies.extensions import db


def get_s3_config():
    """Retrieve S3 bucket configuration from Flask config."""
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        f"{current_app.config['BOTTLE_IMAGE_S3_URL']}/{current_app.config['BOTTLE_IMAGE_S3_KEY']}",
    )


def add_bottle_images(form: BottleAddForm, bottle: Bottle) -> bool:
    """Process image uploads for a bottle"""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    for field_num in range(1, 4):
        image_field = form[f"bottle_image_{field_num}"]
        if not image_field.data:
            continue

        try:
            # Process image
            image = Image.open(image_field.data)
            if image.width > 400:
                ratio = 400 / image.width
                image = image.resize((400, int(image.height * ratio)))

            # Get next available sequence
            sequence = bottle.next_available_sequence

            # Save to S3
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)

            s3_client.put_object(
                Body=buffer,
                Bucket=img_s3_bucket,
                Key=f"{img_s3_key}/{bottle.id}_{sequence}.png",
                ContentType="image/png",
            )

            # Add database record
            db.session.add(BottleImage(bottle_id=bottle.id, sequence=sequence))
            db.session.commit()

        except ClientError:
            return False

    return True


def delete_bottle_images(bottle, image_ids=None):
    """Delete specific images or all images for a bottle."""
    images_to_delete = bottle.images
    if image_ids:
        images_to_delete = [img for img in bottle.images if img.id in image_ids]
        s3_client = boto3.client("s3")
        img_s3_bucket, img_s3_key, _ = get_s3_config()

    for img in images_to_delete:
        # Delete from S3
        s3_client.delete_object(
            Bucket=f"{img_s3_bucket}",
            Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.png",
        )

    # Remove from database
    for img in images_to_delete:
        db.session.delete(img)
    db.session.commit()
