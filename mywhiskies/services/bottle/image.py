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

    # Collect all valid image uploads first
    valid_uploads = []
    for field_num in range(1, 4):
        image_field = form[f"bottle_image_{field_num}"]
        if image_field.data:
            valid_uploads.append((field_num, image_field.data))

    # Process images in order
    for sequence, (_, image_data) in enumerate(valid_uploads, start=1):
        try:
            # Process image
            image = Image.open(image_data)
            if image.width > 400:
                ratio = 400 / image.width
                image = image.resize((400, int(image.height * ratio)))

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
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    # Get images to delete
    images_to_delete = bottle.images
    if image_ids:
        images_to_delete = [img for img in bottle.images if img.id in image_ids]

    # Delete from S3 and database
    for img in images_to_delete:
        # Delete from S3
        s3_client.delete_object(
            Bucket=f"{img_s3_bucket}",
            Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.png",
        )
        db.session.delete(img)

    db.session.commit()

    # Resequence remaining images if any images were deleted
    if images_to_delete:
        remaining_images = sorted(
            [img for img in bottle.images if img not in images_to_delete],
            key=lambda x: x.sequence,
        )

        # Resequence remaining images
        for new_seq, img in enumerate(remaining_images, start=1):
            old_seq = img.sequence
            if old_seq != new_seq:
                # Rename in S3
                s3_client.copy_object(
                    Bucket=f"{img_s3_bucket}",
                    CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{old_seq}.png",
                    Key=f"{img_s3_key}/{bottle.id}_{new_seq}.png",
                )
                s3_client.delete_object(
                    Bucket=f"{img_s3_bucket}",
                    Key=f"{img_s3_key}/{bottle.id}_{old_seq}.png",
                )
                # Update sequence in database
                img.sequence = new_seq

        db.session.commit()
