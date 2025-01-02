import uuid
from unittest.mock import MagicMock, patch

from flask import Flask, url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage, MultiDict

from mywhiskies.blueprints.bottle.forms import BottleAddForm
from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from mywhiskies.services.bottle.form import prep_bottle_form
from mywhiskies.services.bottle.image import add_bottle_images


def create_bottle_formdata(
    test_user: User, file_storage: FileStorage = None
) -> MultiDict:
    """Create the form data for adding a bottle."""
    formdata = MultiDict(
        {
            "name": "Frey Ranch " "Farm Strength" "",
            "type": "BOURBON",
            "year_barrelled": 2018,
            "year_bottled": 2023,
            "abv": 62.15,
            "cost": 79.99,
            "stars": "4.5",
            "description": "Cask strength straight bourbon whiskey.",
            "review": "This bottle can go toe-to-toe with most Frey Ranch SiB offerings",
            "distilleries": [str(test_user.distilleries[0].id)],
            "bottler_id": "0",
            "is_private": False,
        }
    )
    if file_storage:
        formdata.add("bottle_image_1", file_storage)
    return formdata


def test_add_bottle_requires_login(
    app: Flask, client: FlaskClient, test_user_01: User
) -> None:
    # loading the form should fail.
    response = client.get(
        url_for("bottle.bottle_add"),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]

    # make sure the form can't be submitted in any other way.
    test_user_bottle_count = len(test_user_01.bottles)
    formdata = create_bottle_formdata(test_user_01)
    response = client.post(
        url_for("bottle.bottle_add"),
        data=formdata,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)
    # verify that the bottle was _not_ added
    assert test_user_bottle_count == len(test_user_01.bottles)


def test_valid_bottle_form(app: Flask, test_user_01: User, mock_image: str) -> None:
    with open(mock_image, "rb") as f:
        file_storage = FileStorage(
            stream=f, filename="test_image.png", content_type="image/png"
        )
        formdata = create_bottle_formdata(test_user_01, file_storage)

        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
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
