import os
import sys

import pytest
from flask import Flask, url_for
from flask.testing import FlaskClient
from flask_login import logout_user
from sqlalchemy.orm import scoped_session, sessionmaker

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
def session(app):
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
def test_client(app: Flask) -> FlaskClient:
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def test_user_01() -> User:
    """
    Create a test user with associated objects.
    2 Bottlers: Lost Lantern and Crowded Barrel Whiskey Co.
    2 Distilleries: Frey Ranch and Lexington Brewing and Distilling Co.
    1 Bottle: Frey Ranch Straight Rye Whiskey

    Can delete Crowded Barrel Whiskey Co., as there are no related bottles.
    Can delete Lexington Brewing and Distilling Co. as there are no related bottles.
    """
    user = User(
        username="test_user_01",
        email="test_user_01@example.com",
        email_confirmed=True,
    )
    user.set_password(TEST_USER_PASSWORD)
    db.session.add(user)
    db.session.commit()

    # incorrect information below. will fix later when testing edit a bottler.
    bottler = Bottler(
        name="Lost Lantern",
        description="An independent bottler.",
        region_1="Vergenes",
        region_2="VS",
        url="https://lostlantern.com",
        user_id=user.id,
    )
    db.session.add(bottler)
    db.session.commit()

    # this bottler has no bottles. We should be able to delete it.
    bottler = Bottler(
        name="Crowded Barrel Whiskey Co.",
        description="The world's first crowdsourced whiskey distillery.",
        region_1="Austin",
        region_2="TX",
        url="https://crowdedbarrelwhiskey.com",
        user_id=user.id,
    )
    db.session.add(bottler)
    db.session.commit()

    # incorrect information below. will fix later when testing edit a distillery.
    distillery = Distillery(
        name="Frey Ranh",
        description="A distillery in Nevda.",
        region_1="Nevada",
        region_2="USA",
        url="https://frey.com",
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

    # this distillery has no bottles. We should be able to delete it.
    distillery = Distillery(
        name="Ironroot Republic",
        description="A family-owned Texas distillery.",
        region_1="Denison",
        region_2="TX",
        url="https://ironrootrepublic.com",
        user_id=user.id,
    )
    db.session.add(distillery)
    db.session.commit()

    return user


@pytest.fixture
def test_user_02() -> User:
    """Create a test user for testing how logged in users interact with other users' data."""
    user = User(
        username="test_user_02",
        email="test_user_02@example.com",
        email_confirmed=True,
    )
    user.set_password("TestUser0002")
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
        description="A distillery in Nevda.",
        region_1="Fallon",
        region_2="NV",
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


@pytest.fixture
def logged_in_user(client: FlaskClient, test_user_01: User) -> FlaskClient:
    """Log in the test user and return the logged-in client."""
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user_01.username,
            "password": TEST_USER_PASSWORD,
        },
    )
    return client


@pytest.fixture(autouse=True)
def logged_out_user() -> None:
    """Ensure the user is logged out before each test."""
    yield
    logout_user()


def expected_page_title(username: str) -> str:
    suffix = "'s" if not username.endswith("s") else "'"
    return html_encode(f"{username}{suffix} Whiskies")


def html_encode(text: str) -> str:
    """HTML encodes characters in a string in order to be able to search for that string in response.data"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
