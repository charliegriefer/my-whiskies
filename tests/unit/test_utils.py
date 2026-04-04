from unittest.mock import MagicMock

from mywhiskies.services.utils import get_flash_msg, is_my_list


# --- is_my_list ---

def test_is_my_list_authenticated_matching_username(test_user_01) -> None:
    current_user = MagicMock()
    current_user.is_authenticated = True
    current_user.username = test_user_01.username

    assert is_my_list(test_user_01.username, current_user) is True


def test_is_my_list_case_insensitive(test_user_01) -> None:
    current_user = MagicMock()
    current_user.is_authenticated = True
    current_user.username = test_user_01.username

    assert is_my_list(test_user_01.username.upper(), current_user) is True


def test_is_my_list_authenticated_different_username(test_user_01, test_user_02) -> None:
    current_user = MagicMock()
    current_user.is_authenticated = True
    current_user.username = test_user_01.username

    assert is_my_list(test_user_02.username, current_user) is False


def test_is_my_list_not_authenticated(test_user_01) -> None:
    current_user = MagicMock()
    current_user.is_authenticated = False

    assert is_my_list(test_user_01.username, current_user) is False


# --- get_flash_msg ---

def test_get_flash_msg_with_field_errors() -> None:
    form = MagicMock()
    form.errors = {"username": ["This field is required."]}

    result = get_flash_msg(form)

    assert "Please correct the following issue(s):" in result["message"]
    assert "This field is required." in result["message"]
    assert result["reset_errors"] is False


def test_get_flash_msg_with_recaptcha_error() -> None:
    form = MagicMock()
    form.errors = {"recaptcha": ["Please complete the reCAPTCHA."]}

    result = get_flash_msg(form)

    assert result["message"] == "Please complete the reCAPTCHA."
    assert result["reset_errors"] is True


def test_get_flash_msg_with_multiple_errors() -> None:
    form = MagicMock()
    form.errors = {
        "username": ["Too short.", "Invalid characters."],
        "email": ["Not a valid email address."],
    }

    result = get_flash_msg(form)

    assert "Too short." in result["message"]
    assert "Invalid characters." in result["message"]
    assert "Not a valid email address." in result["message"]
