from unittest.mock import MagicMock, patch

from flask import url_for

from mywhiskies.blueprints.user.models import User
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    get_user_by_username,
    log_in_user,
    validate_password,
)
from tests.conftest import TEST_USER_PASSWORD


def test_get_user_by_username(test_user_01: User) -> None:
    user = get_user_by_username(test_user_01.username)
    assert user == test_user_01


def test_validate_password(test_user_01: User) -> None:
    assert validate_password(test_user_01, TEST_USER_PASSWORD)
    assert not validate_password(test_user_01, "wrongpassword")


def test_check_email_confirmation(test_user_01: User) -> None:
    test_user_01.email_confirmed = False
    assert not check_email_confirmation(test_user_01)
    test_user_01.email_confirmed = True
    assert check_email_confirmation(test_user_01)


@patch("mywhiskies.services.auth.login.login_user")
def test_log_in_user(mock_login_user: MagicMock, test_user_01: User) -> None:
    log_in_user(test_user_01, remember_me=True)
    mock_login_user.assert_called_once_with(test_user_01, remember=True)


def test_determine_next_page(test_user_01: User) -> None:
    next_page = determine_next_page(test_user_01, None)
    assert next_page == url_for("core.home", username=test_user_01.username)
    next_page = determine_next_page(test_user_01, "http://example.com/next")
    assert next_page == url_for("core.home", username=test_user_01.username)
    next_page = determine_next_page(test_user_01, "/next")
    assert next_page == "/next"
