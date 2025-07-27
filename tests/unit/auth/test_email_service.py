from unittest.mock import ANY, MagicMock, patch

from mywhiskies.models import User
from mywhiskies.services.auth.email import (
    send_password_reset_email,
    send_registration_confirmation_email,
)


@patch("mywhiskies.services.auth.email.send_email")
def test_send_registration_confirmation_email(
    mock_send_email: MagicMock, test_user_01: User
) -> None:
    send_registration_confirmation_email(test_user_01)
    mock_send_email.assert_called_once_with(
        "Please Confirm Your Email",
        sender="Bartender <bartender@my-whiskies.online>",
        recipients=[test_user_01.email],
        text_body=ANY,  # Ignore the dynamic part
        html_body=ANY,  # Ignore the dynamic part
    )


@patch("mywhiskies.services.auth.email.send_email")
def test_send_password_reset_email(
    mock_send_email: MagicMock, test_user_01: User
) -> None:
    send_password_reset_email(test_user_01)
    mock_send_email.assert_called_once_with(
        "[My Whiskies Online] Reset Your Password",
        sender="Bartender <bartender@my-whiskies.online>",
        recipients=[test_user_01.email],
        text_body=ANY,  # Ignore the dynamic part
        html_body=ANY,  # Ignore the dynamic part
    )
