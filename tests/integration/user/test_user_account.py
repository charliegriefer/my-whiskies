from unittest.mock import patch

from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.models import User


def test_account_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("user.account"))
    assert response.status_code == 302
    assert url_for("auth.login") in response.headers["Location"]


def test_account_shows_user_info(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.get(url_for("user.account"))
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert test_user_01.username in response_data
    assert test_user_01.email in response_data
    # account page displays counts for bottles, bottlers, and distilleries
    assert str(len(test_user_01.bottles)) in response_data
    assert str(len(test_user_01.bottlers)) in response_data
    assert str(len(test_user_01.distilleries)) in response_data


def test_change_email_same_address(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.post(
        url_for("user.change_email"),
        data={"email": test_user_01.email},
        follow_redirects=True,
    )
    assert b"already your current" in response.data


def test_change_email_sends_confirmation(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    with patch("mywhiskies.blueprints.user.views.user.send_email_change_confirmation") as mock_send:
        response = logged_in_user_01.post(
            url_for("user.change_email"),
            data={"email": "brand_new@example.com"},
            follow_redirects=True,
        )
        mock_send.assert_called_once()
        assert b"confirmation email has been sent" in response.data


def test_confirm_email_change_applies_new_email(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    new_email = "confirmed_new@example.com"
    token = test_user_01.get_email_change_token(new_email)
    response = logged_in_user_01.get(
        url_for("user.confirm_email_change", token=token),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert test_user_01.email == new_email


def test_confirm_email_change_bad_token(logged_in_user_01: FlaskClient) -> None:
    response = logged_in_user_01.get(
        url_for("user.confirm_email_change", token="invalid-token"),
        follow_redirects=True,
    )
    assert b"invalid or has expired" in response.data


def test_private_account_hides_from_anonymous(client: FlaskClient, test_user_01: User) -> None:
    test_user_01.is_private = True
    assert client.get(url_for("bottle.list", username=test_user_01.username)).status_code == 404
    assert client.get(url_for("bottler.list", username=test_user_01.username)).status_code == 404
    assert client.get(url_for("distillery.list", username=test_user_01.username)).status_code == 404


def test_private_account_hides_from_other_user(logged_in_user_01: FlaskClient, test_user_02: User) -> None:
    test_user_02.is_private = True
    assert logged_in_user_01.get(url_for("bottle.list", username=test_user_02.username)).status_code == 404


def test_private_account_visible_to_owner(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    test_user_01.is_private = True
    assert logged_in_user_01.get(url_for("bottle.list", username=test_user_01.username)).status_code == 200


def test_set_privacy_toggle(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    assert not test_user_01.is_private
    logged_in_user_01.post(url_for("user.privacy"), data={"is_private": "y"})
    assert test_user_01.is_private
    logged_in_user_01.post(url_for("user.privacy"), data={})
    assert not test_user_01.is_private
