import json

from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.extensions import db
from mywhiskies.models import BarrelPicker, User

# --- page-level add ---


def test_add_page_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("barrel_picker.add"), follow_redirects=False)
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_add_page_renders(logged_in_user_01: FlaskClient) -> None:
    response = logged_in_user_01.get(url_for("barrel_picker.add"))
    assert response.status_code == 200


def test_add_page_creates_picker(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    count_before = len(test_user_01.barrel_pickers)
    response = logged_in_user_01.post(
        url_for("barrel_picker.add"),
        data={"name": "Page Level Picker"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.session.refresh(test_user_01)
    assert len(test_user_01.barrel_pickers) == count_before + 1


def test_add_page_rejects_duplicate(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.add"),
        data={"name": "Total Beverage Solution"},
    )
    assert response.status_code == 200
    assert "already have a barrel picker" in response.get_data(as_text=True)


# --- quick_add ---


def test_quick_add_get_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("barrel_picker.quick_add"), follow_redirects=False)
    assert response.status_code == 302


def test_quick_add_get_returns_form(logged_in_user_01: FlaskClient) -> None:
    response = logged_in_user_01.get(url_for("barrel_picker.quick_add"))
    assert response.status_code == 200
    assert "<form" in response.get_data(as_text=True)


def test_quick_add_post_creates_picker(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    count_before = len(test_user_01.barrel_pickers)
    response = logged_in_user_01.post(
        url_for("barrel_picker.quick_add"),
        data={"name": "Quick Add Picker"},
    )
    assert response.status_code == 200
    db.session.refresh(test_user_01)
    assert len(test_user_01.barrel_pickers) == count_before + 1


def test_quick_add_post_returns_hx_trigger(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.quick_add"),
        data={"name": "Trigger Test Picker"},
    )
    assert response.status_code == 200
    trigger = json.loads(response.headers["HX-Trigger"])
    assert trigger["closeModal"]["id"] == "quickAddBarrelPickerModal"
    assert "newId" in trigger["closeModal"]


def test_quick_add_post_rejects_duplicate(logged_in_user_01: FlaskClient, test_barrel_picker: BarrelPicker) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.quick_add"),
        data={"name": "Total Beverage Solution"},
    )
    assert response.status_code == 200
    assert "already have a barrel picker" in response.get_data(as_text=True)
    assert "HX-Trigger" not in response.headers
