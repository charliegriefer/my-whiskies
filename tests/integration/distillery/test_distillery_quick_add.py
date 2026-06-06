import json

from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.extensions import db
from mywhiskies.models import User

# --- quick_add ---


def test_quick_add_get_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("distillery.quick_add"), follow_redirects=False)
    assert response.status_code == 302


def test_quick_add_get_returns_form(logged_in_user_01: FlaskClient) -> None:
    response = logged_in_user_01.get(url_for("distillery.quick_add"))
    assert response.status_code == 200
    assert "<form" in response.get_data(as_text=True)


def test_quick_add_post_creates_distillery(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    count_before = len(test_user_01.distilleries)
    response = logged_in_user_01.post(
        url_for("distillery.quick_add"),
        data={"name": "Quick Add Distillery"},
    )
    assert response.status_code == 200
    db.session.refresh(test_user_01)
    assert len(test_user_01.distilleries) == count_before + 1


def test_quick_add_post_returns_hx_trigger(logged_in_user_01: FlaskClient) -> None:
    response = logged_in_user_01.post(
        url_for("distillery.quick_add"),
        data={"name": "Trigger Test Distillery"},
    )
    assert response.status_code == 200
    trigger = json.loads(response.headers["HX-Trigger"])
    assert trigger["closeModal"]["id"] == "quickAddDistilleryModal"
    assert "newId" in trigger["closeModal"]


def test_quick_add_post_rejects_duplicate(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    existing_name = test_user_01.distilleries[0].name
    response = logged_in_user_01.post(
        url_for("distillery.quick_add"),
        data={"name": existing_name},
    )
    assert response.status_code == 200
    assert "already have a distillery" in response.get_data(as_text=True)
    assert "HX-Trigger" not in response.headers


# --- options ---


def test_options_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("distillery.options"), follow_redirects=False)
    assert response.status_code == 302


def test_options_returns_json(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.get(url_for("distillery.options"))
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    names = [item["name"] for item in data]
    for distillery in test_user_01.distilleries:
        assert distillery.name in names
