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

DISPLAY_MAX = 1200
JPEG_QUALITY = 85
FULL_JPEG_QUALITY = 95


def get_s3_config():
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        f"{current_app.config['BOTTLE_IMAGE_S3_URL']}/{current_app.config['BOTTLE_IMAGE_S3_KEY']}",
    )


def get_full_s3_config():
    return (
        current_app.config["BOTTLE_IMAGE_S3_BUCKET"],
        current_app.config["BOTTLE_IMAGE_FULL_S3_KEY"],
    )


def _to_resized_jpg_bytes(file_storage) -> bytes:
    file_storage.seek(0)
    img = Image.open(file_storage)
    img = ImageOps.exif_transpose(img)
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


def _to_full_jpg_bytes(file_storage) -> bytes:
    """Full-resolution JPEG — same pipeline as display but without the thumbnail step."""
    file_storage.seek(0)
    img = Image.open(file_storage)
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        background = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        background.paste(img, mask=img.getchannel("A"))
        img = background
    else:
        img = img.convert("RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=FULL_JPEG_QUALITY, optimize=True)
    return out.getvalue()


def _upload_full(s3_client, full_bucket: str, full_key: str, key: str, data: bytes) -> None:
    """Upload to the pro full-res bucket. Failures are non-fatal."""
    try:
        s3_client.put_object(
            Body=data,
            Bucket=full_bucket,
            Key=f"{full_key}/{key}",
            ContentType="image/jpeg",
            CacheControl="public, max-age=31536000",
        )
    except ClientError:
        pass


def _delete_full(s3_client, full_bucket: str, full_key: str, key: str) -> None:
    """Delete from the pro full-res bucket. Failures are non-fatal (key may not exist)."""
    try:
        s3_client.delete_object(Bucket=full_bucket, Key=f"{full_key}/{key}")
    except ClientError:
        pass


def _copy_full(s3_client, full_bucket: str, full_key: str, src_key: str, dst_key: str) -> None:
    try:
        s3_client.copy_object(
            Bucket=full_bucket,
            CopySource=f"{full_bucket}/{full_key}/{src_key}",
            Key=f"{full_key}/{dst_key}",
        )
    except ClientError:
        pass


def process_bottle_images(form, bottle: Bottle, is_pro: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Process the drop-zone form submission: parse `image_order` JSON and apply
    uploads, reordering, and removals in one atomic operation.

    Falls back to `add_bottle_images` when `image_order` is empty (JS disabled).

    Returns (True, None) on success, (False, error_message) on failure.
    """
    image_order_field = getattr(form, "image_order", None)
    image_order_str = (image_order_field.data or "").strip() if image_order_field else ""

    if not image_order_str:
        ok = add_bottle_images(form, bottle, is_pro=is_pro)
        return (True, None) if ok else (False, "An error occurred while uploading images.")

    try:
        image_order = json.loads(image_order_str)
    except (json.JSONDecodeError, ValueError):
        return False, "Invalid image order data."

    if not image_order:
        return True, None

    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    full_bucket, full_key = get_full_s3_config()

    existing_map = {img.id: img for img in bottle.images}
    keep_ids = {item["id"] for item in image_order if item.get("type") == "existing" and item.get("id")}

    for img_id, img in list(existing_map.items()):
        if img_id not in keep_ids:
            try:
                s3_client.delete_object(
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg",
                )
            except ClientError:
                pass
            _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_{img.sequence}.jpg")
            db.session.delete(img)
    db.session.flush()

    kept = {img_id: img for img_id, img in existing_map.items() if img_id in keep_ids}
    orig_seqs = {img_id: img.sequence for img_id, img in kept.items()}

    final_seqs: dict = {}
    for final_seq, item in enumerate(image_order, start=1):
        if item.get("type") == "existing" and item.get("id") in kept:
            final_seqs[item["id"]] = final_seq

    try:
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
                if is_pro:
                    _copy_full(
                        s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg", f"{bottle.id}_tmp_{new_seq}.jpg"
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
                if is_pro:
                    _copy_full(
                        s3_client, full_bucket, full_key, f"{bottle.id}_tmp_{new_seq}.jpg", f"{bottle.id}_{new_seq}.jpg"
                    )
                    _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_tmp_{new_seq}.jpg")
            final_seqs_set = {new_seq for _, new_seq in to_rename.values()}
            for _, (old_seq, _) in to_rename.items():
                if old_seq not in final_seqs_set:
                    s3_client.delete_object(
                        Bucket=img_s3_bucket,
                        Key=f"{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                    )
                    if is_pro:
                        _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg")

        for img in kept.values():
            img.sequence = 10 + img.sequence
            db.session.flush()
        for img_id, new_seq in final_seqs.items():
            kept[img_id].sequence = new_seq
            db.session.flush()

        for final_seq, item in enumerate(image_order, start=1):
            if item.get("type") == "new":
                slot = item.get("slot")
                if slot:
                    ff = getattr(form, f"bottle_image_{slot}", None)
                    if ff and ff.data:
                        if is_pro:
                            full_bytes = _to_full_jpg_bytes(ff.data)
                            _upload_full(s3_client, full_bucket, full_key, f"{bottle.id}_{final_seq}.jpg", full_bytes)
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


def add_bottle_images(form: BottleAddForm, bottle: Bottle, is_pro: bool = False) -> bool:
    """Process image uploads for a bottle (JS-disabled fallback path)."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    full_bucket, full_key = get_full_s3_config()

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

            if is_pro:
                full_bytes = _to_full_jpg_bytes(image_data)
                _upload_full(s3_client, full_bucket, full_key, f"{bottle.id}_{sequence}.jpg", full_bytes)

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

    resequence_bottle_images(bottle, is_pro=is_pro)
    return True


def resequence_bottle_images(bottle, is_pro: bool = False):
    """Ensure all bottle images have sequential sequence numbers without gaps."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    full_bucket, full_key = get_full_s3_config()

    images = sorted(bottle.images, key=lambda img: img.sequence)

    sequence_changes = {}
    for new_seq, img in enumerate(images, start=1):
        if img.sequence != new_seq:
            sequence_changes[img.id] = (img.sequence, new_seq)
            img.sequence = new_seq
            db.session.flush()

    if sequence_changes:
        for _, (old_seq, new_seq) in sequence_changes.items():
            s3_client.copy_object(
                Bucket=img_s3_bucket,
                CopySource=f"{img_s3_bucket}/{img_s3_key}/{bottle.id}_{old_seq}.jpg",
                Key=f"{img_s3_key}/{bottle.id}_temp_{new_seq}.jpg",
            )
            if is_pro:
                _copy_full(
                    s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg", f"{bottle.id}_temp_{new_seq}.jpg"
                )

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
            if is_pro:
                _copy_full(
                    s3_client, full_bucket, full_key, f"{bottle.id}_temp_{new_seq}.jpg", f"{bottle.id}_{new_seq}.jpg"
                )
                _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_temp_{new_seq}.jpg")
                if old_seq != new_seq:
                    _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg")

        db.session.commit()


def delete_bottle_images(bottle, image_ids=None):
    """Delete specific images or all images for a bottle."""
    s3_client = boto3.client("s3")
    img_s3_bucket, img_s3_key, _ = get_s3_config()
    full_bucket, full_key = get_full_s3_config()

    images_to_delete = list(bottle.images)
    if image_ids:
        images_to_delete = [img for img in bottle.images if img.id in image_ids]

    for img in images_to_delete:
        s3_client.delete_object(
            Bucket=img_s3_bucket,
            Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg",
        )
        _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_{img.sequence}.jpg")
        db.session.delete(img)

    db.session.commit()

    remaining_images = (
        db.session.query(BottleImage).filter(BottleImage.bottle_id == bottle.id).order_by(BottleImage.sequence).all()
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
            # Mirror resequence in full bucket regardless of current pro status —
            # user may have been pro when they uploaded.
            _copy_full(s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg", f"{bottle.id}_{new_seq}.jpg")
            _delete_full(s3_client, full_bucket, full_key, f"{bottle.id}_{old_seq}.jpg")
            img.sequence = new_seq
            db.session.flush()

    db.session.commit()
