import uuid
from unittest.mock import MagicMock, patch

from flask import Flask, url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage, MultiDict

from mywhiskies.blueprints.bottle.forms import BottleAddForm
from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from mywhiskies.services.bottle.form import prepare_bottle_form
from mywhiskies.services.bottle.image import add_bottle_images


def test_add_bottle_requires_login(app: Flask, client: FlaskClient) -> None:
    response = client.get(url_for("bottle.bottle_add"), follow_redirects=False)
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottle_form(app: Flask, test_user: User, mock_image: str) -> None:
    with open(mock_image, "rb") as f:
        file_storage = FileStorage(
            stream=f, filename="test_image.png", content_type="image/png"
        )
        formdata = MultiDict(
            {
                "name": "Test Bottle",
                "type": "bourbon",
                "year_barrelled": 2020,
                "year_bottled": 2022,
                "abv": 68.8,
                "cost": 50.00,
                "stars": "5",
                "description": "A fine sample bottle.",
                "review": "Excellent taste.",
                "distilleries": [test_user.distilleries[0].id],
                "bottler_id": "0",
                "bottle_image_1": file_storage,
            }
        )

        form = BottleAddForm()
        prepare_bottle_form(test_user, form)
        form.process(formdata)

        assert form.validate(), f"Form validation failed: {form.errors}"

        with patch("boto3.client") as mock_boto_client, patch(
            "PIL.Image.open"
        ) as mock_image_open:
            mock_image_obj = MagicMock()
            mock_image_open.return_value = mock_image_obj
            mock_image_obj.width = 800
            mock_image_obj.height = 600

            mock_s3_client = MagicMock()
            mock_boto_client.return_value = mock_s3_client

            bottle = Bottle(id=str(uuid.uuid4()))
            result = add_bottle_images(form, bottle)

            assert result is True, "Image upload failed"
            assert mock_s3_client.put_object.called, "S3 put_object was not called"
