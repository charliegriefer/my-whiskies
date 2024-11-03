import pytest
from flask import url_for
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import LoginForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():

        # Delete any existing users with the same username or email
        db.session.execute(db.delete(User).where(User.username == "testuser"))
        db.session.execute(db.delete(User).where(User.email == "test@example.com"))
        db.session.commit()

        # Create the new test user
        user = User(
            username="testuser",
            email="test@example.com",
            email_confirmed=True,
        )
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
    return user


def test_valid_login_form(app, test_user):
    """Test that a valid login form passes validation."""
    formdata = MultiDict(
        {
            "username": "testuser",
            "password": "testpass",
        }
    )
    form = LoginForm(formdata)
    assert form.validate()


def test_empty_username(app):
    """Test that an empty username fails validation."""
    formdata = MultiDict(
        {
            "username": "",
            "password": "testpass",
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()  # Ensure validation fails
    assert "username" in form.errors


def test_empty_password(app):
    """Test that an empty password fails validation."""
    formdata = MultiDict(
        {
            "username": "testuser",
            "password": "",
        }
    )
    form = LoginForm(formdata)
    assert not form.validate()  # Ensure validation fails
    assert "password" in form.errors


def test_invalid_login(app, test_user):
    """Test that incorrect credentials fail the login process."""
    with app.test_client() as client:
        response = client.post(
            url_for("auth.login"),
            data={
                "username": "testuser",
                "password": "wrongpassword",
            },
            follow_redirects=True,  # Follow redirects to capture the final response
        )
        assert response.status_code == 200  # Ensure login page is returned again
        assert (
            b"Incorrect username or password!" in response.data
        )  # Check for error message


def test_valid_login(app, test_user):
    """Test that correct credentials allow the user to log in."""
    with app.test_client() as client:
        response = client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": "testpass",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200  # Ensure the request was successful

        print("*" * 100)
        print(response.data)
        print("*" * 100)

        # Check if the user is redirected to the home page
        assert (
            f"{test_user.username}&#39;s Whiskies".encode() in response.data
        )  # Check for the user's home page content

        # Check for the presence of the logout button
        assert f"Log Out {test_user.username}".encode() in response.data
