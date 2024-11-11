from unittest.mock import patch

import pytest
from flask import url_for

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.auth.login import (
    check_email_confirmation,
    determine_next_page,
    get_user_by_username,
    log_in_user,
    validate_password,
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


def test_get_user_by_username(test_user):
    user = get_user_by_username(test_user.username)
    assert user == test_user


def test_validate_password(test_user):
    assert validate_password(test_user, "testpassword")
    assert not validate_password(test_user, "wrongpassword")


def test_check_email_confirmation(test_user):
    test_user.email_confirmed = False
    assert not check_email_confirmation(test_user)
    test_user.email_confirmed = True
    assert check_email_confirmation(test_user)


@patch("mywhiskies.services.auth.login.login_user")
def test_log_in_user(mock_login_user, test_user):
    log_in_user(test_user, remember_me=True)
    mock_login_user.assert_called_once_with(test_user, remember=True)


def test_determine_next_page(test_user):
    next_page = determine_next_page(test_user, None)
    assert next_page == url_for("core.home", username=test_user.username)
    next_page = determine_next_page(test_user, "http://example.com/next")
    assert next_page == url_for("core.home", username=test_user.username)
    next_page = determine_next_page(test_user, "/next")
    assert next_page == "/next"
