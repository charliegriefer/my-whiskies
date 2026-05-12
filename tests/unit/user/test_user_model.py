from mywhiskies.models import User
from tests.conftest import TEST_USER_PASSWORD


def test_set_password(test_user_01: User) -> None:
    assert test_user_01.password_hash is not None


def test_check_password(test_user_01: User) -> None:
    assert test_user_01.check_password(TEST_USER_PASSWORD)
    assert not test_user_01.check_password("wrongpassword")


def test_mail_confirm_token(test_user_01: User) -> None:
    token = test_user_01.get_mail_confirm_token()
    user = User.verify_mail_confirm_token(token)
    assert user == test_user_01


def test_reset_password_token(test_user_01: User) -> None:
    token = test_user_01.get_reset_password_token()
    user = User.verify_reset_password_token(token)
    assert user == test_user_01


def test_email_change_token(test_user_01: User) -> None:
    new_email = "newemail@example.com"
    token = test_user_01.get_email_change_token(new_email)
    user, returned_email = User.verify_email_change_token(token)
    assert user == test_user_01
    assert returned_email == new_email


def test_email_change_token_invalid() -> None:
    user, email = User.verify_email_change_token("not-a-valid-token")
    assert user is None
    assert email is None
