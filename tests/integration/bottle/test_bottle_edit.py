import copy
from unittest.mock import MagicMock, patch

from flask import url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage, MultiDict

from mywhiskies.blueprints.bottle.forms import BottleEditForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottle.bottle import edit_bottle
from mywhiskies.services.bottle.form import prepare_bottle_form


def test_edit_bottle_requires_login(client: FlaskClient, test_user_01: User) -> None:
    # loading the form should fail.
    response = client.get(
        url_for("bottle.bottle_edit", bottle_id=test_user_01.bottles[0].id),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]

    # make sure the form can't be submitted in any other way.
    bottle_name = test_user_01.bottles[0].name
    formdata = MultiDict({"name": "Updated Bottle Name"})
    response = client.post(
        url_for("bottle.bottle_edit", bottle_id=test_user_01.bottles[0].id),
        data=formdata,
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)
    # verify that the bottle was _not_ updated
    assert bottle_name == test_user_01.bottles[0].name


def test_valid_bottle_edit_form(test_user_01: User, mock_image: str) -> None:
    """Test the validation of a valid bottle edit form with image upload."""
    bottle_to_edit = test_user_01.bottles[0]
    bottle_orig = copy.deepcopy(bottle_to_edit.__dict__)

    # Create a FileStorage object from a mock image
    with open(mock_image, "rb") as f:
        file_storage = FileStorage(
            stream=f, filename="test_image.png", content_type="image/png"
        )
        # Create form data for editing
        formdata = MultiDict(
            {
                "name": "Frey Ranch Straight Rye Whiskey EDITED",
                "type": "rye",
                "year_barrelled": 2017,
                "year_bottled": 2023,
                "abv": 69.8,
                "cost": 114.99,
                "stars": "4",
                "description": "100% Fallon-grown rye greatness",
                "review": "This is so damned good",
                "distilleries": [str(d.id) for d in bottle_to_edit.distilleries],
                "bottler_id": "0",
                "bottle_image_1": file_storage,
            }
        )
        # Create and process the form
        form = BottleEditForm()
        prepare_bottle_form(test_user_01, form)
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
            test_user_01.bottles[0].distilleries = [
                db.session.merge(d) for d in bottle_to_edit.distilleries
            ]

            # Call the edit bottle function
            edit_bottle(form, bottle_to_edit)

        assert bottle_orig.get("name") != bottle_to_edit.name
        assert bottle_orig.get("year_barrelled") != bottle_to_edit.year_barrelled
        assert bottle_orig.get("year_bottled") != bottle_to_edit.year_bottled
        assert bottle_orig.get("abv") != bottle_to_edit.abv
        assert bottle_orig.get("cost") != bottle_to_edit.cost
        assert bottle_orig.get("stars") != bottle_to_edit.stars
        assert bottle_orig.get("description") != bottle_to_edit.description
        assert bottle_orig.get("review") != bottle_to_edit.review
