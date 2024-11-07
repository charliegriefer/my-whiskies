from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def test_edit_bottler_requires_login(client: FlaskClient, test_user: User) -> None:
    response = client.get(
        url_for("bottler.bottler_edit", bottler_id=test_user.bottlers[0].id),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_edit_form(logged_in_user: FlaskClient, test_user: User) -> None:
    client = logged_in_user

    formdata = {
        "name": "Updated Bottler Name",
        "description": "An updated fine bottler.",
        "region_1": "Philadelphia",
        "region_2": "PA",
        "url": "https://www.updatedbottler.com",
    }

    response = client.post(
        url_for("bottler.bottler_edit", bottler_id=test_user.bottlers[0].id),
        data=formdata,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        url_for("bottler.bottlers_list", username=test_user.username)
        in response.request.url
    )

    assert f'"{formdata["name"]}" has been successfully updated.' in response.get_data(
        as_text=True
    )

    updated_bottler = db.session.get(Bottler, test_user.bottlers[0].id)
    assert updated_bottler.name == formdata["name"]
    assert updated_bottler.description == formdata["description"]
    assert updated_bottler.region_1 == formdata["region_1"]
    assert updated_bottler.region_2 == formdata["region_2"]
    assert updated_bottler.url == formdata["url"]
