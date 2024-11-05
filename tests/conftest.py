import os
import sys

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_login import logout_user
from sqlalchemy.orm import scoped_session, sessionmaker

from mywhiskies.blueprints.user.models import User

# Ensure the parent directory is added to the system path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from mywhiskies.app import create_app  # noqa: E402
from mywhiskies.extensions import db  # noqa: E402

TEST_PASSWORD = "testpass"


@pytest.fixture(autouse=True)
def logged_out_user(app: Flask, client: FlaskClient) -> None:
    yield
    logout_user()


@pytest.fixture(scope="session")
def app() -> Flask:
    app = create_app(config_class=TestConfig)
    app.teardown_bkp = app.teardown_appcontext_funcs
    app.teardown_appcontext_funcs = []
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function", autouse=True)
def session(app: Flask) -> scoped_session:
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(bind=connection)
    Session = scoped_session(session_factory)

    db.session = Session

    yield Session

    transaction.rollback()
    connection.close()
    Session.remove()


@pytest.fixture
def test_user(app: Flask) -> User:
    user = User(
        username="testuser",
        email="test@example.com",
        email_confirmed=True,
    )
    user.set_password(TEST_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def login_data(test_user: User) -> dict:
    return {"username": test_user.username, "password": TEST_PASSWORD}
