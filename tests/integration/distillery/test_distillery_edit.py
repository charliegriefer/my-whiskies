from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


def test_edit_distillery_requires_login(
    client: FlaskClient, test_user_01: User
) -> None:
    response = client.get(
        url_for(
            "distillery.distillery_edit", distillery_id=test_user_01.bottlers[0].id
        ),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_distillery_edit_form(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    client = logged_in_user_01

    formdata = {
        "name": "Frey Ranch UPDATED",
        "description": "A distillery in Nevada UPDATED.",
        "region_1": "Fallon UPDATED",
        "region_2": "NV UPDATED",
        "url": "https://freyranch.com/UPDATED",
    }

    response = client.post(
        url_for(
            "distillery.distillery_edit", distillery_id=test_user_01.distilleries[0].id
        ),
        data=formdata,
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        url_for("distillery.distilleries_list", username=test_user_01.username)
        in response.request.url
    )

    assert f'"{formdata["name"]}" has been successfully updated.' in response.get_data(
        as_text=True
    )

    updated_distillery = db.session.get(Distillery, test_user_01.distilleries[0].id)
    assert updated_distillery.name == formdata["name"]
    assert updated_distillery.description == formdata["description"]
    assert updated_distillery.region_1 == formdata["region_1"]
    assert updated_distillery.region_2 == formdata["region_2"]
    assert updated_distillery.url == formdata["url"]
