import os
import tempfile

import pytest
from flask import Flask

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_distillery(app: Flask, test_user: User) -> Distillery:
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
def test_bottle(app: Flask, test_user: User, test_distillery: Distillery) -> Bottle:
    """Create a test bottle linked to the test distillery."""
    bottle = Bottle(
        name="Old Bottle Name",
        type="bourbon",
        year_barrelled=2020,
        year_bottled=2022,
        abv=68.8,
        cost=50.00,
        stars="5",
        description="A fine sample bottle.",
        review="Excellent taste.",
        user_id=test_user.id,
        distilleries=[test_distillery],
    )
    db.session.add(bottle)
    db.session.commit()
    return bottle


@pytest.fixture
def mock_image() -> str:
    """Create a temporary PNG image file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1024)
        temp_file_path = temp_file.name
    yield temp_file_path
    os.remove(temp_file_path)
