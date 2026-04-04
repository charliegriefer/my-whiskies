import copy

from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.extensions import db
from mywhiskies.models import Bottler, User


def test_edit_bottler_requires_login(client: FlaskClient, test_user_01: User) -> None:
    bottler = test_user_01.bottlers[0]
    response = client.get(
        url_for(
            "bottler.edit",
            username=test_user_01.username,
            user_num=bottler.user_num,
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
            "bottler.edit",
            username=test_user_01.username,
            user_num=test_user_01.bottlers[0].user_num,
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


def test_edit_not_my_bottler(
    logged_in_user_01: FlaskClient, test_user_02: User
) -> None:
    """A logged-in user should not be able to edit another user's bottler."""
    client = logged_in_user_01
    bottler = test_user_02.bottlers[0]
    original_name = bottler.name

    response = client.post(
        url_for(
            "bottler.edit",
            username=test_user_02.username,
            user_num=bottler.user_num,
        ),
        data={"name": "Hacked Name", "region_1": "XX", "region_2": "YY"},
        follow_redirects=True,
    )

    assert response.status_code in (403, 200)
    assert bottler.name == original_name
