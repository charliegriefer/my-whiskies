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


def add_bottle_images(form: BottleAddForm, bottle: Bottle, idx: int = None) -> bool:
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
