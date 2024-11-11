import pytest
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import RegistrationForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user(app):
    user = User(username="existinguser", email="existing@example.com")
    user.set_password("testpassword")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


def test_valid_registration_form():
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newPassword1234",
                "password2": "newPassword1234",
                "agree_terms": True,
            }
        )
    )
    assert form.validate(), f"Form validation failed: {form.errors}"


def test_invalid_username_format():
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "invalid user",
                "email": "newuser@example.com",
                "password": "newpassword",
                "password2": "newpassword",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "username" in form.errors


def test_duplicate_username(test_user):
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "existinguser",
                "email": "newuser@example.com",
                "password": "newpassword",
                "password2": "newpassword",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "username" in form.errors


def test_invalid_email_format():
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "invalid-email",
                "password": "newpassword",
                "password2": "newpassword",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "email" in form.errors


def test_duplicate_email(test_user):
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "existing@example.com",
                "password": "newpassword",
                "password2": "newpassword",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "email" in form.errors


def test_password_mismatch():
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword",
                "password2": "differentpassword",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "password2" in form.errors


def test_terms_not_agreed():
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword",
                "password2": "newpassword",
                "agree_terms": False,
            }
        )
    )
    assert not form.validate()
    assert "agree_terms" in form.errors
