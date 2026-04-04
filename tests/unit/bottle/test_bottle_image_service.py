import io
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from PIL import Image

from mywhiskies.extensions import db
from mywhiskies.models import Bottle, BottleImage, BottleTypes, User
from botocore.exceptions import ClientError

from mywhiskies.services.bottle.image import (
    _to_resized_jpg_bytes,
    add_bottle_images,
    delete_bottle_images,
    resequence_bottle_images,
)

DISPLAY_MAX = 1600


# --- helpers ---

def _make_image_file(width=200, height=200, mode="RGB") -> io.BytesIO:
    img = Image.new(mode, (width, height), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _make_rgba_image_file() -> io.BytesIO:
    img = Image.new("RGBA", (200, 200), color=(100, 150, 200, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture
def bottle_with_images(app: Flask, test_user_01: User) -> Bottle:
    bottle = Bottle(
        name="Image Test Bottle",
        type=BottleTypes.BOURBON,
        user_id=test_user_01.id,
    )
    db.session.add(bottle)
    db.session.commit()

    for seq in [1, 2, 3]:
        db.session.add(BottleImage(bottle_id=bottle.id, sequence=seq))
    db.session.commit()

    yield bottle

    for img in list(bottle.images):
        db.session.delete(img)
    if db.session.get(Bottle, bottle.id):
        db.session.delete(bottle)
    db.session.commit()


# --- _to_resized_jpg_bytes ---

def test_to_resized_jpg_bytes_returns_jpeg(app: Flask) -> None:
    result = _to_resized_jpg_bytes(_make_image_file())
    # JPEG magic bytes
    assert result[:2] == b"\xff\xd8"


def test_to_resized_jpg_bytes_large_image_is_resized(app: Flask) -> None:
    large_img = _make_image_file(width=3000, height=3000)
    result = _to_resized_jpg_bytes(large_img)
    output = Image.open(io.BytesIO(result))
    assert max(output.size) <= DISPLAY_MAX


def test_to_resized_jpg_bytes_small_image_not_enlarged(app: Flask) -> None:
    small_img = _make_image_file(width=100, height=100)
    result = _to_resized_jpg_bytes(small_img)
    output = Image.open(io.BytesIO(result))
    assert output.size == (100, 100)


def test_to_resized_jpg_bytes_handles_rgba(app: Flask) -> None:
    result = _to_resized_jpg_bytes(_make_rgba_image_file())
    output = Image.open(io.BytesIO(result))
    assert output.mode == "RGB"


# --- resequence_bottle_images ---

@patch("mywhiskies.services.bottle.image.boto3.client")
def test_resequence_no_changes_when_already_sequential(
    mock_boto: MagicMock, bottle_with_images: Bottle
) -> None:
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    resequence_bottle_images(bottle_with_images)

    # Images are already 1, 2, 3 — no S3 operations needed
    mock_s3.copy_object.assert_not_called()


@patch("mywhiskies.services.bottle.image.boto3.client")
def test_resequence_fixes_gap_in_sequences(
    mock_boto: MagicMock, app: Flask, test_user_01: User
) -> None:
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    bottle = Bottle(
        name="Gap Test Bottle",
        type=BottleTypes.BOURBON,
        user_id=test_user_01.id,
    )
    db.session.add(bottle)
    db.session.commit()

    # Sequences 1 and 3 (gap at 2)
    db.session.add(BottleImage(bottle_id=bottle.id, sequence=1))
    db.session.add(BottleImage(bottle_id=bottle.id, sequence=3))
    db.session.commit()

    resequence_bottle_images(bottle)

    sequences = sorted(img.sequence for img in bottle.images)
    assert sequences == [1, 2]

    # S3 copy/delete should have been called to renumber sequence 3 → 2
    assert mock_s3.copy_object.called


# --- delete_bottle_images ---

@patch("mywhiskies.services.bottle.image.boto3.client")
def test_delete_all_images(
    mock_boto: MagicMock, bottle_with_images: Bottle
) -> None:
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    delete_bottle_images(bottle_with_images)

    remaining = (
        db.session.query(BottleImage)
        .filter(BottleImage.bottle_id == bottle_with_images.id)
        .all()
    )
    assert len(remaining) == 0


@patch("mywhiskies.services.bottle.image.boto3.client")
def test_delete_specific_image(
    mock_boto: MagicMock, bottle_with_images: Bottle
) -> None:
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3

    image_to_delete = bottle_with_images.images[0]
    delete_bottle_images(bottle_with_images, image_ids=[image_to_delete.id])

    remaining = (
        db.session.query(BottleImage)
        .filter(BottleImage.bottle_id == bottle_with_images.id)
        .all()
    )
    assert len(remaining) == 2


# --- add_bottle_images: S3 error path ---

@patch("mywhiskies.services.bottle.image.boto3.client")
def test_add_bottle_images_returns_false_on_s3_error(
    mock_boto: MagicMock, app: Flask, test_user_01: User
) -> None:
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}, "PutObject"
    )
    mock_boto.return_value = mock_s3

    bottle = Bottle(
        name="S3 Error Bottle",
        type=BottleTypes.BOURBON,
        user_id=test_user_01.id,
    )
    db.session.add(bottle)
    db.session.commit()

    form = MagicMock()
    form.__getitem__ = MagicMock(side_effect=lambda key: (
        MagicMock(data=_make_image_file()) if key == "bottle_image_1"
        else MagicMock(data=None)
    ))

    result = add_bottle_images(form, bottle)
    assert result is False
