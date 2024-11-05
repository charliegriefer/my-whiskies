import pytest
from flask import Flask

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user_bottler(app: Flask, test_user: User) -> Bottler:
    """Create a test bottler."""
    bottler = Bottler(
        name="Lost Lantern",
        description="The best independent bottler.",
        region_1="Vergennes",
        region_2="VT",
        url="https://lostlanternwhiskey.com",
        user_id=test_user.id,
    )
    db.session.add(bottler)
    db.session.commit()
    return bottler


@pytest.fixture
def test_user_distillery(app: Flask, test_user: User) -> Distillery:
    """Create a test distillery."""
    distillery = Distillery(
        name="Frey Ranch",
        description="A distillery in Nevada.",
        region_1="Nevada",
        region_2="USA",
        url="https://freyranch.com",
        user_id=test_user.id,
    )
    db.session.add(distillery)
    db.session.commit()
    return distillery


@pytest.fixture
def test_user_bottle(
    app: Flask,
    test_user: User,
    test_user_distillery: Distillery,
    test_user_bottler: Bottler,
) -> Bottle:
    """Create a test bottle linked to the test distillery."""
    bottle = Bottle(
        name="Frey Ranch Three Grain Straight Bourbon Whiskey",
        type="bourbon",
        year_barrelled=2017,
        year_bottled=2022,
        abv=59.10,
        cost=99.00,
        stars="5",
        description="No wheat, high rye.",
        user_id=test_user.id,
        bottler_id=test_user_bottler.id,
        distilleries=[test_user_distillery],
    )
    db.session.add(bottle)
    db.session.commit()
    return bottle


@pytest.fixture
def npc_user(app: Flask) -> User:
    """Create a separate user with a distillery and a bottle."""
    user = User(
        username="NPCUser",
        email="npc@example.com",
        email_confirmed=True,
    )
    user.set_password("npcPass1234")
    db.session.add(user)
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

    bottler = Bottler(
        name="Lost Lantern",
        description="The best independent bottler.",
        region_1="Vergennes",
        region_2="VT",
        url="https://lostlanternwhiskey.com",
        user_id=user.id,
    )

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


def html_encode(text: str) -> str:
    """HTML encodes characters in a string in order to be able to search for that string in response.data"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
