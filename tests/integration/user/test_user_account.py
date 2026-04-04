from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import User


def test_account_requires_login(client: FlaskClient) -> None:
    response = client.get(url_for("user.account"))
    assert response.status_code == 302
    assert url_for("auth.login") in response.headers["Location"]


def test_account_shows_user_info(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    response = logged_in_user_01.get(url_for("user.account"))
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert test_user_01.username in response_data
    assert test_user_01.email in response_data
    # account page displays counts for bottles, bottlers, and distilleries
    assert str(len(test_user_01.bottles)) in response_data
    assert str(len(test_user_01.bottlers)) in response_data
    assert str(len(test_user_01.distilleries)) in response_data
