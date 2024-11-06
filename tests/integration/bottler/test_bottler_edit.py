from flask import Flask, url_for

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from tests.conftest import TEST_PASSWORD


def test_edit_bottler_requires_login(app: Flask, test_user_bottler: Bottler) -> None:
    with app.test_client() as client:
        response = client.get(
            url_for("bottler.bottler_edit", bottler_id=test_user_bottler.id),
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_edit_form(
    app: Flask, test_user: User, test_user_bottler: Bottler
) -> None:
    with app.test_client() as client:
        # Log in the test user
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )

        formdata = {
            "name": "Updated Bottler Name",
            "description": "An updated fine bottler.",
            "region_1": "Philadelphia",
            "region_2": "PA",
            "url": "https://www.updatedbottler.com",
        }

        response = client.post(
            url_for("bottler.bottler_edit", bottler_id=test_user_bottler.id),
            data=formdata,
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert (
            url_for("bottler.bottlers_list", username=test_user.username)
            in response.request.url
        )

        assert (
            bytes(
                f'"{formdata["name"]}" has been successfully updated.', encoding="utf-8"
            )
            in response.data
        )

        updated_bottler = db.session.get(Bottler, test_user_bottler.id)
        assert updated_bottler.name == formdata["name"]
        assert updated_bottler.description == formdata["description"]
        assert updated_bottler.region_1 == formdata["region_1"]
        assert updated_bottler.region_2 == formdata["region_2"]
        assert updated_bottler.url == formdata["url"]
