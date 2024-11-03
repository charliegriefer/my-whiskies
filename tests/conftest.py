import os
import sys

import pytest

from mywhiskies.blueprints.user.models import User

# Ensure the parent directory is added to the system path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from mywhiskies.app import create_app  # noqa: E402

# from mywhiskies.blueprints.user.models import User  # noqa: E402
from mywhiskies.extensions import db  # noqa: E402

TEST_PASSWORD = "testpass"


@pytest.fixture(scope="session")
def app():
    app = create_app(config_class=TestConfig)
    app.teardown_bkp = app.teardown_appcontext_funcs
    app.teardown_appcontext_funcs = []
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def transaction(app):
    """Wrap each test in a transaction and roll back after."""
    connection = db.engine.connect()
    transaction = connection.begin()
    db.session.remove()
    db.configure_mappers()

    yield  # This is where the test will run

    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(app):
    with app.app_context():
        # delete any existing users with the same username or email
        db.session.execute(db.delete(User).where(User.username == "testuser"))
        db.session.execute(db.delete(User).where(User.email == "test@example.com"))
        db.session.commit()

        user = User(
            username="testuser",
            email="test@example.com",
            email_confirmed=True,
        )
        user.set_password(TEST_PASSWORD)
        db.session.add(user)
        db.session.commit()
    yield user

    with app.app_context():
        db.session.execute(db.delete(User).where(User.username == "testuser"))
        db.session.commit()


@pytest.fixture
def login_data(test_user):
    return {"username": test_user.username, "password": TEST_PASSWORD}
