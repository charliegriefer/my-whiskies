import pytest
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import ResetPasswordRequestForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():

        # Delete any existing users with the same username or email
        db.session.execute(db.delete(User).where(User.username == "testuser"))
        db.session.execute(db.delete(User).where(User.email == "test@example.com"))
        db.session.commit()

        # Create the new test user
        user = User(
            username="testuser",
            email="test@example.com",
            email_confirmed=True,
        )
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
    return user


def test_reset_password_request_form_valid(app, test_user):
    formdata = MultiDict(
        {
            "form_name": "reset_pw_request",
            "email": test_user.email,
        }
    )
    form = ResetPasswordRequestForm(formdata)
    foo = form.validate()
    print(form.errors)
    assert foo


def test_reset_password_request_form_invalid_email(app):
    formdata = MultiDict(
        {
            "email": "invalid-email",
        }
    )
    form = ResetPasswordRequestForm(formdata)
    assert not form.validate()
    assert "email" in form.errors
