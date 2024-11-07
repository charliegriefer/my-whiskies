import os
import tempfile

import pytest
from flask import Flask

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user_bottle_to_delete(app: Flask, test_user: User) -> Bottle:
    """Create a test bottle for test_user to delete."""
    with app.app_context():
        bottle = Bottle(
            name="Frey Ranch Oat Whiskey",
            type="american_whiskey",
            year_barrelled=2018,
            year_bottled=2022,
            abv=52.5,
            cost=99.00,
            stars="2",
            description="Not really my jam.",
            user_id=test_user.id,
            distilleries=[test_user.distilleries[0]],
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
