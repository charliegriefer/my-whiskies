from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.models import BarrelPicker, User


def test_list_anonymous(client: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker) -> None:
    response = client.get(url_for("barrel_picker.list", username=test_user_01.username))
    assert response.status_code == 200
    assert "Total Beverage Solution" in response.get_data(as_text=True)


def test_list_empty_state(client: FlaskClient, test_user_01: User) -> None:
    response = client.get(url_for("barrel_picker.list", username=test_user_01.username))
    assert response.status_code == 200
    assert "no barrel pickers" in response.get_data(as_text=True)


def test_list_owner_sees_add_button(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.get(url_for("barrel_picker.list", username=test_user_01.username))
    assert "Add Barrel Picker" in response.get_data(as_text=True)


def test_list_non_owner_no_add_button(logged_in_user_02: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_02.get(url_for("barrel_picker.list", username=test_user_01.username))
    assert "Add Barrel Picker" not in response.get_data(as_text=True)


def test_list_404_for_unknown_user(client: FlaskClient) -> None:
    response = client.get(url_for("barrel_picker.list", username="nobody"))
    assert response.status_code == 404
