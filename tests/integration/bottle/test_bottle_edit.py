from unittest.mock import MagicMock, patch

from flask import url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage, MultiDict

from mywhiskies.blueprints.bottle.forms import BottleEditForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottle.bottle import edit_bottle
from mywhiskies.services.bottle.form import prepare_bottle_form


def test_edit_bottle_requires_login(client: FlaskClient, test_user: User) -> None:
    # loading the form should fail.
    response = client.get(
        url_for("bottle.bottle_edit", bottle_id=test_user.bottles[0].id),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]

    # make sure the form can't be submitted in any other way.
    bottle_name = test_user.bottles[0].name
    formdata = MultiDict({"name": "Updated Bottle Name"})
    response = client.post(
        url_for("bottle.bottle_edit", bottle_id=test_user.bottles[0].id),
        data=formdata,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)
    # verify that the bottle was _not_ updated
    assert bottle_name == test_user.bottles[0].name


def test_valid_bottle_edit_form(
    test_user: User,
    mock_image: str,
) -> None:
    """Test the validation of a valid bottle edit form with image upload."""
    test_bottle = test_user.bottles[0]

    # Create a FileStorage object from a mock image
    with open(mock_image, "rb") as f:
        file_storage = FileStorage(
            stream=f, filename="test_image.png", content_type="image/png"
        )
        # Create form data for editing
        formdata = MultiDict(
            {
                "name": "Updated Bottle Name",
                "type": "bourbon",
                "year_barrelled": 2021,
                "year_bottled": 2023,
                "abv": 70.0,
                "cost": 60.00,
                "stars": "4",
                "description": "An updated fine sample bottle.",
                "review": "Still excellent taste.",
                "distilleries": [str(d.id) for d in test_bottle.distilleries],
                "bottler_id": "0",
                "bottle_image_1": file_storage,
            }
        )
        # Create and process the form
        form = BottleEditForm()
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

            # Ensure the distillery object is attached to the session
            test_user.bottles[0].distilleries = [
                db.session.merge(d) for d in test_bottle.distilleries
            ]

            # Call the edit bottle function
            edit_bottle(form, test_bottle)
