from flask import url_for

from mywhiskies.blueprints.user.models import User
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    get_user_by_username,
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


def test_determine_next_page(test_user_01: User) -> None:
    next_page = determine_next_page(test_user_01, None)
    assert next_page == url_for("core.main")
    next_page = determine_next_page(test_user_01, "http://example.com/next")
    assert next_page == url_for("core.main")
    next_page = determine_next_page(test_user_01, "/next")
    assert next_page == "/next"
