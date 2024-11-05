import os
import tempfile

import pytest
from flask import Flask

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


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
    app: Flask, test_user: User, test_user_distillery: Distillery
) -> Bottle:
    """Create a test bottle linked to the test distillery."""
    bottle = Bottle(
        name="Frey Ranch Straight Rye Whiskey",
        type="bourbon",
        year_barrelled=2017,
        year_bottled=2023,
        abv=62.5,
        cost=89.00,
        stars="5",
        description="Only just the best bourbon ever bottled.",
        review="If I could give this 6 stars, I would.",
        user_id=test_user.id,
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
def mock_image() -> str:
    """Create a temporary PNG image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)
        temp_file_path = temp_file.name
    yield temp_file_path
    os.remove(temp_file_path)
