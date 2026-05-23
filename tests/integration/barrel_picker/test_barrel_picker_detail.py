from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.models import BarrelPicker, User


def test_detail_anonymous(client: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker) -> None:
    response = client.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    assert response.status_code == 200
    assert "Total Beverage Solution" in response.get_data(as_text=True)


def test_detail_shows_no_bottles_text(
    client: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = client.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    assert "no bottles picked by Total Beverage Solution" in response.get_data(as_text=True)


def test_detail_owner_sees_edit_delete(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Edit" in body
    assert "Delete" in body


def test_detail_non_owner_no_edit_delete(
    logged_in_user_02: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_02.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "bi-pencil" not in body
    assert "bi-trash" not in body


def test_detail_shows_associated_bottle(
    client: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    from mywhiskies.extensions import db

    bottle = test_user_01.bottles[0]
    test_barrel_picker.bottles = [bottle]
    db.session.commit()

    response = client.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    assert bottle.name in response.get_data(as_text=True)


def test_detail_404_for_unknown_picker(client: FlaskClient, test_user_01: User) -> None:
    response = client.get(
        url_for("barrel_picker.detail", username=test_user_01.username, user_num=9999)
    )
    assert response.status_code == 404
