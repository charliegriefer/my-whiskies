import os
import sys

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_login import logout_user

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User

# Ensure the parent directory is added to the system path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from mywhiskies.app import create_app  # noqa: E402
from mywhiskies.extensions import db  # noqa: E402

TEST_USER_PASSWORD = "testpass"


@pytest.fixture()
def app() -> Flask:
    app = create_app(config_class=TestConfig)
    app.teardown_bkp = app.teardown_appcontext_funcs
    app.teardown_appcontext_funcs = []
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


# @pytest.fixture(scope="function", autouse=True)
# def session(app: Flask) -> scoped_session:
#     """Create a new database session for a test."""
#     connection = db.engine.connect()
#     transaction = connection.begin()
#     session_factory = sessionmaker(bind=connection)
#     Session = scoped_session(session_factory)
#     db.session = Session

#     yield Session

#     transaction.rollback()
#     connection.close()
#     Session.remove()


@pytest.fixture
def test_user() -> User:
    """
    A test user that we'll be using frequently throughout our tests.
    This user has one distillery, two bottlers, and one bottle.
    """
    user = User(
        username="test_user",
        email="test@example.com",
        email_confirmed=True,
    )
    user.set_password(TEST_USER_PASSWORD)
    db.session.add(user)
    db.session.commit()

    bottler = Bottler(
        name="Lost Lantern",
        description="The best independent bottler.",
        region_1="Vergennes",
        region_2="VT",
        url="https://lostlanternwhiskey.com",
        user_id=user.id,
    )
    db.session.add(bottler)
    db.session.commit()

    bottler = Bottler(
        name="Two Souls Spirits",
        description="A bottler without any bottles",
        region_1="Davie",
        region_2="FL",
        url="https://twosoulsspirits.com",
        user_id=user.id,
    )
    db.session.add(bottler)
    db.session.commit()

    distillery = Distillery(
        name="Frey Ranch",
        description="A distillery in Nevada.",
        region_1="Nevada",
        region_2="USA",
        url="https://freyranch.com",
        user_id=user.id,
    )
    db.session.add(distillery)
    db.session.commit()

    bottle = Bottle(
        name="Frey Ranch Straight Rye Whiskey",
        type="rye",
        year_barrelled=2018,
        year_bottled=2024,
        abv=68.8,
        cost=114.00,
        stars="5",
        description="100% Fallon-grown rye goodness",
        user_id=user.id,
        distilleries=[distillery],
        bottler_id=bottler.id,
    )
    db.session.add(bottle)
    db.session.commit()
    return user


@pytest.fixture
def npc_user() -> User:
    """
    A test user similar to the one above.
    This user exists for our main test_user to be able to attempt deleting another user's objects.
    """
    user = User(
        username="npc_user",
        email="npc@example.com",
        email_confirmed=True,
    )
    user.set_password("npcPass1234")
    db.session.add(user)
    db.session.commit()

    bottler = Bottler(
        name="Lost Lantern",
        description="The best independent bottler.",
        region_1="Vergennes",
        region_2="VT",
        url="https://lostlanternwhiskey.com",
        user_id=user.id,
    )
    db.session.add(bottler)
    db.session.commit()

    distillery = Distillery(
        name="Frey Ranch",
        description="A distillery in Nevada.",
        region_1="Nevada",
        region_2="USA",
        url="https://freyranch.com",
        user_id=user.id,
    )
    db.session.add(distillery)
    db.session.commit()

    bottle = Bottle(
        name="Frey Ranch Straight Rye Whiskey",
        type="rye",
        year_barrelled=2018,
        year_bottled=2024,
        abv=68.8,
        cost=114.00,
        stars="5",
        description="100% Fallon-grown rye goodness",
        user_id=user.id,
        distilleries=[distillery],
    )
    db.session.add(bottle)
    db.session.commit()
    return user


@pytest.fixture(autouse=True)
def logged_out_user() -> None:
    """Ensure the user is logged out before each test."""
    yield
    logout_user()


def html_encode(text: str) -> str:
    """HTML encodes characters in a string in order to be able to search for that string in response.data"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
