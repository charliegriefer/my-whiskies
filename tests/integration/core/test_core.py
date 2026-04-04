from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import User


def test_main_logged_out(client: FlaskClient) -> None:
    response = client.get(url_for("core.main"))
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "My Whiskies Online" in response_data
    # "Join Us!" register prompt is shown to unauthenticated users
    assert "Join Us!" in response_data


def test_main_logged_in(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    response = logged_in_user_01.get(url_for("core.main"))
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert test_user_01.username in response_data
    # "Join Us!" prompt is hidden from authenticated users
    assert "Join Us!" not in response_data


def test_terms(client: FlaskClient) -> None:
    response = client.get(url_for("core.terms"))
    assert response.status_code == 200


def test_privacy(client: FlaskClient) -> None:
    response = client.get(url_for("core.privacy"))
    assert response.status_code == 200


def test_cookies(client: FlaskClient) -> None:
    response = client.get(url_for("core.cookies"))
    assert response.status_code == 200
