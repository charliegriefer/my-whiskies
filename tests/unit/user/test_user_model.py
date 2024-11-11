import pytest

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("testpassword")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


def test_set_password(test_user):
    assert test_user.password_hash is not None


def test_check_password(test_user):
    assert test_user.check_password("testpassword")
    assert not test_user.check_password("wrongpassword")


def test_mail_confirm_token(test_user):
    token = test_user.get_mail_confirm_token()
    user = User.verify_mail_confirm_token(token)
    assert user == test_user


def test_reset_password_token(test_user):
    token = test_user.get_reset_password_token()
    user = User.verify_reset_password_token(token)
    assert user == test_user
