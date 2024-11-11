from unittest.mock import ANY, patch

import pytest

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.auth.password import (
    find_user_for_password_reset,
    flash_password_reset_instructions,
    flash_password_reset_success,
    reset_user_password,
    verify_reset_password_token,
)


@pytest.fixture
def test_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("testpassword")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


def test_find_user_for_password_reset(test_user):
    user = find_user_for_password_reset(test_user.email)
    assert user == test_user


def test_verify_reset_password_token(test_user):
    token = test_user.get_reset_password_token()
    user = verify_reset_password_token(token)
    assert user == test_user


def test_reset_user_password(test_user):
    reset_user_password(test_user, "newpassword")
    assert test_user.check_password("newpassword")


@patch("mywhiskies.services.auth.password.flash")
def test_flash_password_reset_instructions(mock_flash):
    flash_password_reset_instructions()
    mock_flash.assert_called_once_with(
        ANY,  # Ignore the dynamic part
        "info",
    )


@patch("mywhiskies.services.auth.password.flash")
def test_flash_password_reset_success(mock_flash):
    flash_password_reset_success()
    mock_flash.assert_called_once_with("Your password has been reset.", "success")
