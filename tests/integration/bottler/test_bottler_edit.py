import copy

from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def test_edit_bottler_requires_login(client: FlaskClient, test_user_01: User) -> None:
    response = client.get(
        url_for(
            "bottler.bottler_edit",
            username=test_user_01.username,
            bottler_id=test_user_01.bottlers[0].id,
        ),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_edit_form(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    client = logged_in_user_01

    bottler_to_edit = test_user_01.bottlers[0]
    bottler_orig = copy.deepcopy(bottler_to_edit.__dict__)

    formdata = {
        "name": "Lost Lantern UPDATED",
        "description": "An independent bottler UPDATED.",
        "region_1": "Vergennes UPDATED",
        "region_2": "VT UPDATED",
        "url": "https://www.lostlanternwhiskey.com/UPDATED",
    }

    response = client.post(
        url_for(
            "bottler.bottler_edit",
            username=test_user_01.username,
            bottler_id=test_user_01.bottlers[0].id,
        ),
        data=formdata,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        url_for("bottler.list", username=test_user_01.username) in response.request.url
    )

    assert f'"{formdata["name"]}" has been successfully updated.' in response.get_data(
        as_text=True
    )

    updated_bottler = db.session.get(Bottler, test_user_01.bottlers[0].id)
    assert bottler_orig.get("name") != updated_bottler.name
    assert bottler_orig.get("description") != updated_bottler.description
    assert bottler_orig.get("region_1") != updated_bottler.region_1
    assert bottler_orig.get("region_2") != updated_bottler.region_2
    assert bottler_orig.get("url") != updated_bottler.url
