import io
import json
from typing import Optional, Tuple

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


def process_bottle_images(form, bottle: Bottle) -> Tuple[bool, Optional[str]]:
    """
    Process the drop-zone form submission: parse `image_order` JSON and apply
    uploads, reordering, and removals in one atomic operation.

    Falls back to `add_bottle_images` when `image_order` is empty (JS disabled).

    Returns (True, None) on success, (False, error_message) on failure.
    """
    image_order_field = getattr(form, "image_order", None)
    image_order_str = (image_order_field.data or "").strip() if image_order_field else ""

    if not image_order_str:
        # JS-disabled fallback: process bottle_image_1/2/3 in slot order.
        ok = add_bottle_images(form, bottle)
        return (True, None) if ok else (False, "An error occurred while uploading images.")

    try:
        image_order = json.loads(image_order_str)
    except (json.JSONDecodeError, ValueError):
        return False, "Invalid image order data."

    if not image_order:
        return True, None

    # Server-side file-size validation before touching anything.
    max_bytes = current_app.config.get("MAX_FILE_UPLOAD_BYTES", 10 * 1024 * 1024)
    max_mb = current_app.config.get("MAX_FILE_UPLOAD_MB", 10)
    for item in image_order:
        if item.get("type") == "new":
            slot = item.get("slot")
            if slot:
                ff = getattr(form, f"bottle_image_{slot}", None)
                if ff and ff.data:
                    ff.data.seek(0, 2)
                    size = ff.data.tell()
                    ff.data.seek(0)
                    if size > max_bytes:
                        return False, f"One or more images exceed the {max_mb}MB size limit."

    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()

    # Build map of current existing images.
    existing_map = {img.id: img for img in bottle.images}
    keep_ids = {
        item["id"]
        for item in image_order
        if item.get("type") == "existing" and item.get("id")
    }

    # Delete images that are no longer in the order.
    for img_id, img in list(existing_map.items()):
        if img_id not in keep_ids:
            try:
                s3_client.delete_object(
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg",
                )
            except ClientError:
                pass  # Non-fatal; DB record still cleaned up.
            db.session.delete(img)
    db.session.flush()

    kept = {img_id: img for img_id, img in existing_map.items() if img_id in keep_ids}
    orig_seqs = {img_id: img.sequence for img_id, img in kept.items()}

    # Compute final sequences for kept existing images.
    final_seqs: dict = {}
    for final_seq, item in enumerate(image_order, start=1):
        if item.get("type") == "existing" and item.get("id") in kept:
            final_seqs[item["id"]] = final_seq

    try:
        # S3: rename existing images whose sequence changes (two-phase to avoid conflicts).
        to_rename = {
            img_id: (orig_seqs[img_id], new_seq)
            for img_id, new_seq in final_seqs.items()
            if orig_seqs[img_id] != new_seq
        }
        if to_rename:
            for img_id, (old_seq, new_seq) in to_rename.items():
                s3_client.copy_object(
                    Bucket=img_s3_bucket,
                    CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                    Key=f"{img_s3_key}/{bottle.id}_tmp_{new_seq}.jpg",
                )
            for img_id, (old_seq, new_seq) in to_rename.items():
                s3_client.copy_object(
                    Bucket=img_s3_bucket,
                    CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_tmp_{new_seq}.jpg",
                    Key=f"{img_s3_key}/{bottle.id}_{new_seq}.jpg",
                )
                s3_client.delete_object(
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{bottle.id}_tmp_{new_seq}.jpg",
                )
            # Phase 3: delete old keys that are not a final destination of any rename.
            final_seqs_set = {new_seq for _, new_seq in to_rename.values()}
            for _, (old_seq, _) in to_rename.items():
                if old_seq not in final_seqs_set:
                    s3_client.delete_object(
                        Bucket=img_s3_bucket,
                        Key=f"{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                    )

        # DB: reassign sequences (temp offset avoids UNIQUE constraint conflicts).
        for img in kept.values():
            img.sequence = 10 + img.sequence
            db.session.flush()
        for img_id, new_seq in final_seqs.items():
            kept[img_id].sequence = new_seq
            db.session.flush()

        # Upload new images at their final positions.
        for final_seq, item in enumerate(image_order, start=1):
            if item.get("type") == "new":
                slot = item.get("slot")
                if slot:
                    ff = getattr(form, f"bottle_image_{slot}", None)
                    if ff and ff.data:
                        jpg_bytes = _to_resized_jpg_bytes(ff.data)
                        s3_client.put_object(
                            Body=jpg_bytes,
                            Bucket=img_s3_bucket,
                            Key=f"{img_s3_key}/{bottle.id}_{final_seq}.jpg",
                            ContentType="image/jpeg",
                            CacheControl="public, max-age=31536000",
                        )
                        db.session.add(BottleImage(bottle_id=bottle.id, sequence=final_seq))
                        db.session.flush()

        db.session.commit()
        return True, None

    except (ClientError, OSError, ValueError):
        db.session.rollback()
        return False, "An error occurred while uploading images."


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
            db.session.flush()

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
            db.session.flush()

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
