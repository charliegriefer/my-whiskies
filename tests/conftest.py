import os
import sys
from typing import Generator

import pytest
from flask import Flask, url_for
from flask.testing import FlaskClient
from flask_login import logout_user
from mywhiskies.database import init_db
from mywhiskies.extensions import db
from mywhiskies.models import Bottle, Bottler, Distillery, User
from sqlalchemy.orm import scoped_session, sessionmaker

# Ensure the parent directory is added to the system path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from mywhiskies.app import create_app  # noqa: E402

TEST_USER_PASSWORD = "testpass"


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    app = create_app(config_class=TestConfig)
    with app.app_context():
        init_db()
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
def test_user_01() -> "User":  # noqa: F821
    """
    Create a test user (test_user_01) with associated objects:
        - 4 Distilleries: Frey Ranch, Still Austin, Ironroot Republic, and Boulder Spirits
        - 2 Bottlers: Lost Lantern and Crowded Barrel Whiskey Co.
        - 2 Bottles: Frey Ranch Straight Rye Whiskey and Far-Flung Bourbon

    Expectations:
        - Can delete distillery Boulder Spirits, as there are no related bottles.
        - Cannot delete distilleries Frey Ranch or Still Austin as there are related bottles.
        - Can delete bottler Crowded Barrel Whiskey Co., as there are no related bottles.
        - Cannot delete bottler Lost Lantern as there is a related bottle.
        - Far-Flung Bourbon has two distilleries (Frey Ranch and Still Austin):
            - Edit to add a third (Boulder Spirits) and ensure that the bottle now has 3 distilleries.
            - Edit to remove one distillery (Frey Ranch) and ensure that there is only one distillery.
    """

    test_user_01 = User(
        username="test_user_01",
        email="test_user_01@example.com",
        email_confirmed=True,
    )
    test_user_01.set_password(TEST_USER_PASSWORD)
    db.session.add(test_user_01)
    db.session.commit()

    # create user's distilleries
    boulder_spirits = _boulder_spirits()
    boulder_spirits.user_id = test_user_01.id

    frey_ranch = _frey_ranch()
    frey_ranch.user_id = test_user_01.id

    ironroot_republic = _ironroot_republic()
    ironroot_republic.user_id = test_user_01.id

    still_austin = _still_austin()
    still_austin.user_id = test_user_01.id

    db.session.add(boulder_spirits)
    db.session.add(frey_ranch)
    db.session.add(ironroot_republic)
    db.session.add(still_austin)
    db.session.commit()

    # create user's bottlers
    lost_lantern = _lost_lantern()
    lost_lantern.user_id = test_user_01.id

    crowded_barrel = _crowded_barrel()
    crowded_barrel.user_id = test_user_01.id

    db.session.add(lost_lantern)
    db.session.add(crowded_barrel)
    db.session.commit()

    # create user's bottles
    far_flung_bourbon = _far_flung_bourbon()
    far_flung_bourbon.bottler_id = lost_lantern.id
    far_flung_bourbon.distilleries = [frey_ranch, still_austin]
    far_flung_bourbon.user_id = test_user_01.id

    frey_ranch_straight_rye = _frey_ranch_straight_rye()
    frey_ranch_straight_rye.distilleries = [frey_ranch]
    frey_ranch_straight_rye.user_id = test_user_01.id

    ironroot_hubris_hazmat = _ironroot_hubris_hazmat_private()
    ironroot_hubris_hazmat.distilleries = [ironroot_republic]
    ironroot_hubris_hazmat.user_id = test_user_01.id

    db.session.add(far_flung_bourbon)
    db.session.add(frey_ranch_straight_rye)
    db.session.add(ironroot_hubris_hazmat)
    db.session.commit()

    return test_user_01


@pytest.fixture
def test_user_02() -> "User":  # noqa: F821
    """
    Create a test user (test_user_02) with associated objects:
        - 2 Distilleries: Frey Ranch and Ironroot Republic
        - 1 Bottler: Crowded Barrel Whiskey Co.
        - 1 Bottle: Frey Ranch Straight Rye Whiskey

    Expectations:
        - test_user_01 should _not_ be able to manipulate any of these objects.
    """
    from mywhiskies.models import User

    test_user_02 = User(
        username="test_user_02",
        email="test_user_02@example.com",
        email_confirmed=True,
    )
    test_user_02.set_password(TEST_USER_PASSWORD)
    db.session.add(test_user_02)
    db.session.commit()

    # create user's distilleries
    frey_ranch = _frey_ranch()
    frey_ranch.user_id = test_user_02.id

    ironroot_republic = _ironroot_republic()
    ironroot_republic.user_id = test_user_02.id

    # create user's bottlers
    crowded_barrel = _crowded_barrel()
    crowded_barrel.user_id = test_user_02.id

    db.session.add(frey_ranch)
    db.session.add(ironroot_republic)
    db.session.add(crowded_barrel)
    db.session.commit()

    # create user's bottles
    frey_ranch_straight_rye = _frey_ranch_straight_rye()
    frey_ranch_straight_rye.distilleries = [frey_ranch]
    frey_ranch_straight_rye.user_id = test_user_02.id

    frey_ranch_hazmat = _frey_ranch_hazmat_private()
    frey_ranch_hazmat.distilleries = [frey_ranch]
    frey_ranch_hazmat.user_id = test_user_02.id

    db.session.add(frey_ranch_straight_rye)
    db.session.add(frey_ranch_hazmat)
    db.session.commit()

    return test_user_02


@pytest.fixture
def logged_in_user_01(
    client: FlaskClient, test_user_01: "User"  # noqa: F821
) -> FlaskClient:
    """Log in test_user_01 and return the logged-in client."""
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user_01.username,
            "password": TEST_USER_PASSWORD,
        },
    )
    return client


@pytest.fixture
def logged_in_user_02(
    client: FlaskClient, test_user_02: "User"  # noqa: F821
) -> FlaskClient:
    """Log in test_user_02 and return the logged-in client."""
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user_02.username,
            "password": TEST_USER_PASSWORD,
        },
    )
    return client


@pytest.fixture(autouse=True)
def logged_out_user() -> Generator[None, None, None]:
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


# ***** Helper functions to create objects for testing *****


# Distilleries
def _boulder_spirits() -> "Distillery":  # noqa: F821

    return Distillery(
        name="Boulder Spirits",
        description="A distillery in Colorado.",
        region_1="Boulder",
        region_2="CO",
    )


def _frey_ranch() -> "Distillery":  # noqa: F821

    return Distillery(
        name="Frey Ranch",
        description="A distillery in Nevda.",
        region_1="Fallon",
        region_2="NV",
        url="https://freyranch.com",
    )


def _ironroot_republic() -> "Distillery":  # noqa: F821

    return Distillery(
        name="Ironroot Republic",
        description="A family-owned Texas distillery.",
        region_1="Denison",
        region_2="TX",
        url="https://ironrootrepublic.com",
    )


def _still_austin() -> "Distillery":  # noqa: F821

    return Distillery(
        name="Still Austin",
        description="A distillery in Texas.",
        region_1="Austin",
        region_2="TX",
        url="https://www.stillaustin.com",
    )


#  Bottlers
def _crowded_barrel() -> "Bottler":  # noqa: F821

    return Bottler(
        name="Crowded Barrel Whiskey Co.",
        description="The world's first crowdsourced whiskey distillery.",
        region_1="Austin",
        region_2="TX",
        url="https://crowdedbarrelwhiskey.com",
    )


def _lost_lantern() -> "Bottler":  # noqa: F821

    return Bottler(
        name="Lost Lantern",
        description="The best independent bottler.",
        region_1="Vergennes",
        region_2="VT",
        url="https://lostlanternwhiskey.com",
    )


# Bottles
def _far_flung_bourbon() -> "Bottle":  # noqa: F821

    return Bottle(
        name="Far-Flung Bourbon I",
        type="BOURBON",
        abv=68.4,
        description="A blend of straight bourbons from different distilleries.",
    )


def _frey_ranch_straight_rye() -> "Bottle":  # noqa: F821

    return Bottle(
        name="Frey Ranch Straight Rye Whiskey",
        type="RYE",
        year_barrelled=2018,
        year_bottled=2024,
        abv=68.8,
        cost=114.00,
        stars="5",
        description="100% Fallon-grown rye goodness",
        personal_note="This bottle is in my office desk drawer.",
        bottler_id="0",
    )


def _frey_ranch_hazmat_private() -> "Bottle":  # noqa: F821

    return Bottle(
        name="Frey Ranch Straight Bourbon Whiskey",
        type="BOURBON",
        bottler_id="0",
        is_private=True,
    )


def _ironroot_hubris_hazmat_private() -> "Bottle":  # noqa: F821

    return Bottle(
        name="Ironroot Republic Hubris Hazmat",
        type="AMERICAN_WHISKEY",
        bottler_id="0",
        is_private=True,
    )
