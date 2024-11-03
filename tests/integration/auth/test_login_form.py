from flask import url_for
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import LoginForm


def test_valid_login_form(app, login_data: dict):
    """Test that a valid login form passes validation."""
    formdata = MultiDict(
        {
            "username": login_data["username"],
            "password": login_data["password"],
        }
    )
    form = LoginForm(formdata)
    assert form.validate()


def test_empty_username(app, login_data):
    """Test that an empty username fails validation."""
    formdata = MultiDict(
        {
            "username": "",
            "password": login_data["password"],
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()  # Ensure validation fails
    assert "username" in form.errors


def test_empty_password(app, login_data):
    """Test that an empty password fails validation."""
    formdata = MultiDict(
        {
            "username": login_data["username"],
            "password": "",
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()  # Ensure validation fails
    assert "password" in form.errors


def test_invalid_login(app, login_data):
    """Test that incorrect credentials fail the login process."""
    with app.test_client() as client:
        response = client.post(
            url_for("auth.login"),
            data={
                "username": login_data["username"],
                "password": "wrongpassword",
            },
            follow_redirects=True,  # Follow redirects to capture the final response
        )
        assert response.status_code == 200  # Ensure login page is returned again
        assert b"Incorrect username or password!" in response.data


def test_valid_login(app, test_user, login_data):
    """Test that correct credentials allow the user to log in."""
    with app.test_client() as client:
        response = client.post(
            url_for("auth.login"),
            data={
                "username": login_data["username"],
                "password": login_data["password"],
            },
            follow_redirects=True,
        )
        assert response.status_code == 200  # Ensure the request was successful

        # Check if the user is redirected to the home page
        assert (
            f"{test_user.username}&#39;s Whiskies".encode() in response.data
        )  # Check for the user's home page content

        # Check for the presence of the logout button
        assert f"Log Out {test_user.username}".encode() in response.data
