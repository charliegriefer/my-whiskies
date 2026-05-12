from flask import url_for

from mywhiskies.models import User
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    get_user_by_username,
    is_new_ip,
    record_login,
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


def test_is_new_ip_no_prior_logins(test_user_01: User) -> None:
    assert not is_new_ip(test_user_01.id, "1.2.3.4")


def test_is_new_ip_known_ip(test_user_01: User) -> None:
    record_login(test_user_01.id, "1.2.3.4")
    assert not is_new_ip(test_user_01.id, "1.2.3.4")


def test_is_new_ip_unknown_ip(test_user_01: User) -> None:
    record_login(test_user_01.id, "1.2.3.4")
    assert is_new_ip(test_user_01.id, "9.9.9.9")


def test_record_login(test_user_01: User) -> None:
    record_login(test_user_01.id, "1.2.3.4")
    assert len(test_user_01.logins) == 1
    assert test_user_01.logins[0].ip_address == "1.2.3.4"
