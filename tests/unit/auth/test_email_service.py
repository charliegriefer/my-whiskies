from unittest.mock import ANY, patch

import pytest

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.auth.email import (
    send_password_reset_email,
    send_registration_confirmation_email,
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


@patch("mywhiskies.services.auth.email.send_email")
def test_send_registration_confirmation_email(mock_send_email, test_user):
    send_registration_confirmation_email(test_user)
    mock_send_email.assert_called_once_with(
        "Please Confirm Your Email",
        sender="Bartender <bartender@my-whiskies.online>",
        recipients=[test_user.email],
        text_body=ANY,  # Ignore the dynamic part
        html_body=ANY,  # Ignore the dynamic part
    )


@patch("mywhiskies.services.auth.email.send_email")
def test_send_password_reset_email(mock_send_email, test_user):
    send_password_reset_email(test_user)
    mock_send_email.assert_called_once_with(
        "[My Whiskies Online] Reset Your Password",
        sender="Bartender <bartender@my-whiskies.online>",
        recipients=[test_user.email],
        text_body=ANY,  # Ignore the dynamic part
        html_body=ANY,  # Ignore the dynamic part
    )
