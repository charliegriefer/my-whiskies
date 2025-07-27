from flask import Flask, url_for
from flask.testing import FlaskClient
from sqlalchemy import select
from werkzeug.datastructures import MultiDict

from mywhiskies.extensions import db
from mywhiskies.forms.auth import ResetPWForm
from mywhiskies.models import User
from tests.conftest import TEST_USER_PASSWORD


def test_reset_password_valid_token(
    app: Flask, client: FlaskClient, test_user_01: User
) -> None:
    with app.app_context():
        response = client.post(
            url_for(
                "auth.reset_password", token=test_user_01.get_reset_password_token()
            ),
            data={"password": "NewPassword123", "password2": "NewPassword123"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert "Your password has been reset" in response.get_data(as_text=True)

        # verify the password has been updated
        user = (
            db.session.execute(select(User).filter_by(username=test_user_01.username))
            .scalars()
            .first()
        )
        assert user.check_password("NewPassword123")
        assert not user.check_password(TEST_USER_PASSWORD)


def test_valid_password_reset() -> None:
    formdata = MultiDict({"password": "NewPassword123", "password2": "NewPassword123"})
    form = ResetPWForm(formdata)
    assert form.validate()


def assert_invalid_password_reset(
    password: str, password2: str, expected_error: str, field_name: str
) -> None:
    formdata = MultiDict({"password": password, "password2": password2})
    form = ResetPWForm(formdata)
    assert not form.validate()
    assert field_name in form.errors
    assert expected_error in form.errors[field_name]


def test_invalid_password_reset_different_passwords() -> None:
    assert_invalid_password_reset(
        "NewPassword123",
        "DifferentPassword123",
        "Passwords do not match.",
        "password2",
    )


def test_invalid_password_reset_password_too_short() -> None:
    assert_invalid_password_reset(
        "Short1",
        "Short1",
        "Password does not meet the defined requirements.",
        "password",
    )


def test_invalid_password_reset_password_contains_space() -> None:
    assert_invalid_password_reset(
        "Password 1234",
        "Password 1234",
        "Password does not meet the defined requirements.",
        "password",
    )


def test_invalid_password_reset_password_no_lowercase() -> None:
    assert_invalid_password_reset(
        "PASSWORD1234",
        "PASSWORD1234",
        "Password does not meet the defined requirements.",
        "password",
    )


def test_invalid_password_reset_password_no_uppercase() -> None:
    assert_invalid_password_reset(
        "password1234",
        "password1234",
        "Password does not meet the defined requirements.",
        "password",
    )


def test_invalid_password_reset_password_no_numbers() -> None:
    assert_invalid_password_reset(
        "PasswordABC",
        "PasswordABC",
        "Password does not meet the defined requirements.",
        "password",
    )
