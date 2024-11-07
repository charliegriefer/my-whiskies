from flask import Flask, url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import LoginForm
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_USER_PASSWORD


def test_valid_login_form(app: Flask, test_user: User) -> None:
    """Test that a valid login form passes validation."""
    formdata = MultiDict(
        {"username": test_user.username, "password": TEST_USER_PASSWORD}
    )
    form = LoginForm(formdata)
    assert form.validate()


def test_empty_username(app: Flask) -> None:
    """Test that an empty username fails validation."""
    formdata = MultiDict(
        {
            "username": "",
            "password": TEST_USER_PASSWORD,
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()
    assert "username" in form.errors


def test_empty_password(app: Flask, test_user: User) -> None:
    """Test that an empty password fails validation."""
    formdata = MultiDict(
        {
            "username": test_user.username,
            "password": "",
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()
    assert "password" in form.errors


def test_invalid_login(app: Flask, client: FlaskClient, test_user: User) -> None:
    """Test that incorrect credentials fail the login process."""
    response = client.post(
        url_for("auth.login"),
        data={"username": test_user.username, "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Incorrect username or password!" in response.get_data(as_text=True)


def test_valid_login(
    app: Flask,
    client: FlaskClient,
    test_user: User,
):
    """Test that correct credentials allow the user to log in."""
    response = client.post(
        url_for("auth.login"),
        data={"username": test_user.username, "password": TEST_USER_PASSWORD},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert f"{test_user.username}&#39;s Whiskies" in response.get_data(as_text=True)
    assert f"Log Out {test_user.username}" in response.get_data(as_text=True)
