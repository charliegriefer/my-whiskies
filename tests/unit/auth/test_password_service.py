from unittest.mock import ANY, MagicMock, patch

from mywhiskies.blueprints.user.models import User
from mywhiskies.services.auth.password import (
    find_user_for_password_reset,
    flash_password_reset_instructions,
    flash_password_reset_success,
    reset_user_password,
    verify_reset_password_token,
)


def test_find_user_for_password_reset(test_user_01: User) -> None:
    user = find_user_for_password_reset(test_user_01.email)
    assert user == test_user_01


def test_verify_reset_password_token(test_user_01: User) -> None:
    token = test_user_01.get_reset_password_token()
    user = verify_reset_password_token(token)
    assert user == test_user_01


def test_reset_user_password(test_user_01: User) -> None:
    reset_user_password(test_user_01, "newpassword")
    assert test_user_01.check_password("newpassword")


@patch("mywhiskies.services.auth.password.flash")
def test_flash_password_reset_instructions(mock_flash: MagicMock) -> None:
    flash_password_reset_instructions()
    mock_flash.assert_called_once_with(ANY, "info")


@patch("mywhiskies.services.auth.password.flash")
def test_flash_password_reset_success(mock_flash: MagicMock) -> None:
    flash_password_reset_success()
    mock_flash.assert_called_once_with("Your password has been reset.", "success")
