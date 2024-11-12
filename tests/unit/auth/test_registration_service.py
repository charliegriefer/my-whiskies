from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import RegistrationForm
from mywhiskies.blueprints.user.models import User


def test_valid_registration_form() -> None:
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


def test_invalid_username_format() -> None:
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


def test_duplicate_username(test_user_01: User) -> None:
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": test_user_01.username,
                "email": "newuser@example.com",
                "password": "NewPassword1234",
                "password2": "NewPassword1234",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "username" in form.errors


def test_invalid_email_format() -> None:
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "newuser",
                "email": "invalid-email",
                "password": "NewPassword1234",
                "password2": "NewPassword1234",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "email" in form.errors


def test_duplicate_email(test_user_01: User) -> None:
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "whiskey_guy_42069",
                "email": test_user_01.email,
                "password": "NewPassword1234",
                "password2": "NewPassword1234",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "email" in form.errors


def test_password_mismatch() -> None:
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "whiskey_guy_42069",
                "email": "newuser@example.com",
                "password": "NewPassword1234",
                "password2": "NewPassword12345",
                "agree_terms": True,
            }
        )
    )
    assert not form.validate()
    assert "password2" in form.errors


def test_terms_not_agreed() -> None:
    form = RegistrationForm(
        formdata=MultiDict(
            {
                "username": "whiskey_guy_42069",
                "email": "newuser@example.com",
                "password": "NewPassword1234",
                "password2": "NewPassword1234",
                "agree_terms": False,
            }
        )
    )
    assert not form.validate()
    assert "agree_terms" in form.errors
