import os
import tempfile

import pytest
from flask import Flask, url_for
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.bottle.forms import BottleAddForm
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottle.form import prepare_bottle_form


@pytest.fixture
def test_distillery(app: Flask, test_user: User) -> Distillery:
    with app.app_context():
        distillery = Distillery(
            name="Frey Ranch",
            description="A distillery in Nevada.",
            region_1="Nevada",
            region_2="USA",
            url="https://freyranch.com",
            user_id=test_user.id,
        )
        db.session.add(distillery)
        db.session.commit()
    return distillery


@pytest.fixture
def mock_image():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)
        temp_file_path = temp_file.name
    yield temp_file_path
    os.remove(temp_file_path)


def test_add_bottle_requires_login(app):
    with app.test_client() as client:
        # Attempt to access the add bottle page without logging in
        response = client.get(url_for("bottle.bottle_add"), follow_redirects=False)

        # Check if the response status code is 302 (redirection)
        assert response.status_code == 302

        # Check if the location header points to the login page
        assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottle_form(
    app: Flask, test_user: User, test_distillery: Distillery, mock_image: str
) -> None:
    form = BottleAddForm()
    prepare_bottle_form(test_user, form)

    with open(mock_image, "rb") as img_file:
        formdata = MultiDict(
            {
                "name": "Frey Ranch Single Barrel Bourbon",
                "url": "https://shop.freyranch.com",
                "type": "bourbon",
                "distilleries": [test_distillery.id],
                "bottler_id": "0",
                "size": 750,
                "year_barrelled": 2020,
                "year_bottled": 2022,
                "abv": 68.8,
                "cost": 50.00,
                "stars": "5",
                "description": "A fine sample bottle.",
                "review": "Excellent taste.",
                "bottle_image_1": (img_file, "test_image.png"),
            }
        )
        form.process(formdata)
        assert form.validate()
