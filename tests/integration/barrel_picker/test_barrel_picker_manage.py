import json

from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.extensions import db
from mywhiskies.models import BarrelPicker, User


# --- manage ---


def test_manage_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("barrel_picker.manage"), follow_redirects=False)
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_manage_returns_picker_list(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(url_for("barrel_picker.manage"))
    assert response.status_code == 200
    assert "Total Beverage Solution" in response.get_data(as_text=True)


# --- options ---


def test_options_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("barrel_picker.options"), follow_redirects=False)
    assert response.status_code == 302


def test_options_returns_json(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(url_for("barrel_picker.options"))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    names = [item["name"] for item in data]
    assert "Total Beverage Solution" in names


# --- add ---


def test_add_requires_login(client: FlaskClient) -> None:
    response = client.post(url_for("barrel_picker.add"), follow_redirects=False)
    assert response.status_code == 302


def test_add_creates_picker(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    count_before = len(test_user_01.barrel_pickers)
    response = logged_in_user_01.post(
        url_for("barrel_picker.add"),
        data={"name": "New Test Picker"},
    )
    assert response.status_code == 200
    db.session.refresh(test_user_01)
    assert len(test_user_01.barrel_pickers) == count_before + 1


def test_add_shows_new_picker_in_response(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.add"),
        data={"name": "Spec's Wines Spirits & Finer Foods"},
    )
    assert "Spec&#39;s Wines Spirits &amp; Finer Foods" in response.get_data(as_text=True) or \
           "Spec" in response.get_data(as_text=True)


# --- edit-form ---


def test_edit_form_requires_login(client: FlaskClient, test_barrel_picker: BarrelPicker) -> None:
    response = client.get(
        url_for("barrel_picker.edit_form", user_num=test_barrel_picker.user_num), follow_redirects=False
    )
    assert response.status_code == 302


def test_edit_form_returns_form(
    logged_in_user_01: FlaskClient, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(
        url_for("barrel_picker.edit_form", user_num=test_barrel_picker.user_num)
    )
    assert response.status_code == 200
    assert "Total Beverage Solution" in response.get_data(as_text=True)


# --- modal-edit ---


def test_modal_edit_requires_login(client: FlaskClient, test_barrel_picker: BarrelPicker) -> None:
    response = client.post(
        url_for("barrel_picker.modal_edit", user_num=test_barrel_picker.user_num), follow_redirects=False
    )
    assert response.status_code == 302


def test_modal_edit_updates_picker(
    logged_in_user_01: FlaskClient, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.modal_edit", user_num=test_barrel_picker.user_num),
        data={"name": "Total Bev UPDATED"},
    )
    assert response.status_code == 200
    db.session.refresh(test_barrel_picker)
    assert test_barrel_picker.name == "Total Bev UPDATED"


def test_modal_edit_wrong_user_404(
    logged_in_user_02: FlaskClient, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_02.post(
        url_for("barrel_picker.modal_edit", user_num=test_barrel_picker.user_num),
        data={"name": "Hijacked"},
    )
    assert response.status_code == 404


# --- delete-confirm ---


def test_delete_confirm_requires_login(client: FlaskClient, test_barrel_picker: BarrelPicker) -> None:
    response = client.get(
        url_for("barrel_picker.delete_confirm", user_num=test_barrel_picker.user_num), follow_redirects=False
    )
    assert response.status_code == 302


def test_delete_confirm_no_bottles(
    logged_in_user_01: FlaskClient, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(
        url_for("barrel_picker.delete_confirm", user_num=test_barrel_picker.user_num)
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Total Beverage Solution" in body
    assert "cannot be undone" in body


def test_delete_confirm_with_bottles_shows_warning(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    test_barrel_picker.bottles = [test_user_01.bottles[0]]
    db.session.commit()

    response = logged_in_user_01.get(
        url_for("barrel_picker.delete_confirm", user_num=test_barrel_picker.user_num)
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "associated with" in body


# --- delete ---


def test_delete_requires_login(client: FlaskClient, test_barrel_picker: BarrelPicker) -> None:
    response = client.get(
        url_for("barrel_picker.delete", user_num=test_barrel_picker.user_num), follow_redirects=False
    )
    assert response.status_code == 302


def test_delete_removes_picker(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    picker_id = test_barrel_picker.id
    response = logged_in_user_01.get(
        url_for("barrel_picker.delete", user_num=test_barrel_picker.user_num), follow_redirects=True
    )
    assert response.status_code == 200
    assert db.session.get(BarrelPicker, picker_id) is None


def test_delete_with_bottles_clears_associations(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    bottle = test_user_01.bottles[0]
    bottle_id = bottle.id
    test_barrel_picker.bottles = [bottle]
    db.session.commit()

    picker_id = test_barrel_picker.id
    logged_in_user_01.get(
        url_for("barrel_picker.delete", user_num=test_barrel_picker.user_num), follow_redirects=True
    )
    assert db.session.get(BarrelPicker, picker_id) is None
    assert db.session.get(type(bottle), bottle_id) is not None


def test_delete_wrong_user_404(
    logged_in_user_02: FlaskClient, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_02.get(
        url_for("barrel_picker.delete", user_num=test_barrel_picker.user_num)
    )
    assert response.status_code == 404


# --- full-page edit ---


def test_full_page_edit_requires_login(
    client: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = client.get(
        url_for("barrel_picker.edit", username=test_user_01.username, user_num=test_barrel_picker.user_num),
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_full_page_edit_wrong_user_403(
    logged_in_user_02: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_02.get(
        url_for("barrel_picker.edit", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    assert response.status_code == 403


def test_full_page_edit_get_renders_form(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.get(
        url_for("barrel_picker.edit", username=test_user_01.username, user_num=test_barrel_picker.user_num)
    )
    assert response.status_code == 200
    assert "Total Beverage Solution" in response.get_data(as_text=True)


def test_full_page_edit_post_updates_picker(
    logged_in_user_01: FlaskClient, test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    response = logged_in_user_01.post(
        url_for("barrel_picker.edit", username=test_user_01.username, user_num=test_barrel_picker.user_num),
        data={"name": "Full Page Updated"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    db.session.refresh(test_barrel_picker)
    assert test_barrel_picker.name == "Full Page Updated"
