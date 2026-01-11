import io

import boto3
from botocore.exceptions import ClientError
from flask import current_app
from PIL import Image, ImageOps

from mywhiskies.extensions import db
from mywhiskies.forms.bottle import BottleAddForm
from mywhiskies.models import Bottle, BottleImage


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

    valid_uploads = []
    for field_num in range(1, 4):
        image_field = form[f"bottle_image_{field_num}"]
        if image_field.data:
            valid_uploads.append(image_field.data)

    if not valid_uploads:
        return True

    existing_sequences = [img.sequence for img in bottle.images]
    next_sequence = max(existing_sequences, default=0) + 1

    try:
        for image_data in valid_uploads:
            sequence = next_sequence
            next_sequence += 1

            jpg_bytes = _to_resized_jpg_bytes(image_data)

            s3_client.put_object(
                Body=jpg_bytes,
                Bucket=img_s3_bucket,
                Key=f"{img_s3_key}/{bottle.id}_{sequence}.jpg",
                ContentType="image/jpeg",
                CacheControl="public, max-age=31536000",
            )

            db.session.add(BottleImage(bottle_id=bottle.id, sequence=sequence))

        db.session.commit()

    except (ClientError, OSError, ValueError):
        db.session.rollback()
        return False

    resequence_bottle_images(bottle)
    return True


def resequence_bottle_images(bottle):
    """Ensure all bottle images have sequential sequence numbers without gaps."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    images = sorted(bottle.images, key=lambda img: img.sequence)

    sequence_changes = {}
    for new_seq, img in enumerate(images, start=1):
        if img.sequence != new_seq:
            sequence_changes[img.id] = (img.sequence, new_seq)
            img.sequence = new_seq

    if sequence_changes:
        # Copy to temporary keys first (avoid collisions)
        for _, (old_seq, new_seq) in sequence_changes.items():
            s3_client.copy_object(
                Bucket=img_s3_bucket,
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                Key=f"{img_s3_key}/{bottle.id}_temp_{new_seq}.jpg",
            )

        # Move temp -> final, delete temp + old
        for _, (old_seq, new_seq) in sequence_changes.items():
            s3_client.copy_object(
                Bucket=img_s3_bucket,
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_temp_{new_seq}.jpg",
                Key=f"{img_s3_key}/{bottle.id}_{new_seq}.jpg",
            )

            s3_client.delete_object(
                Bucket=img_s3_bucket,
                Key=f"{img_s3_key}/{bottle.id}_temp_{new_seq}.jpg",
            )

            if old_seq != new_seq:
                s3_client.delete_object(
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                )

        db.session.commit()


def delete_bottle_images(bottle, image_ids=None):
    """Delete specific images or all images for a bottle."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    # Get images to delete
    images_to_delete = list(bottle.images)
    if image_ids:
        images_to_delete = [img for img in bottle.images if img.id in image_ids]

    # Delete from S3 and database
    for img in images_to_delete:
        # Delete from S3
        s3_client.delete_object(
            Bucket=f"{img_s3_bucket}",
            Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg",
        )
        db.session.delete(img)

    db.session.commit()

    # Resequence remaining images (fetch fresh from DB)
    remaining_images = (
        db.session.query(BottleImage)
        .filter(BottleImage.bottle_id == bottle.id)
        .order_by(BottleImage.sequence)
        .all()
    )

    for new_seq, img in enumerate(remaining_images, start=1):
        old_seq = img.sequence
        if old_seq != new_seq:
            s3_client.copy_object(
                Bucket=img_s3_bucket,
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                Key=f"{img_s3_key}/{bottle.id}_{new_seq}.jpg",
            )
            s3_client.delete_object(
                Bucket=img_s3_bucket,
                Key=f"{img_s3_key}/{bottle.id}_{old_seq}.jpg",
            )
            img.sequence = new_seq

    db.session.commit()


DISPLAY_MAX = 1600
JPEG_QUALITY = 85


def _to_resized_jpg_bytes(file_storage) -> bytes:
    """
    Accepts any Pillow-supported upload (png/jpg/etc).
    Returns resized JPEG bytes suitable for web display.
    """
    img = Image.open(file_storage)
    img = ImageOps.exif_transpose(img)

    # Flatten transparency for PNGs (JPEG has no alpha)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        background.paste(img, mask=img.getchannel("A"))
        img = background
    else:
        img = img.convert("RGB")

    img.thumbnail((DISPLAY_MAX, DISPLAY_MAX), resample=Image.Resampling.LANCZOS)

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return out.getvalue()
