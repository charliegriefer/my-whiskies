import pytest

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("testpassword")
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


@pytest.fixture
def test_bottler(app, test_user):
    bottler = Bottler(
        name="Test Bottler",
        region_1="Region 1",
        region_2="Region 2",
        user_id=test_user.id,
    )
    db.session.add(bottler)
    db.session.commit()
    yield bottler
    db.session.delete(bottler)
    db.session.commit()


def test_bottler_creation(test_bottler):
    assert test_bottler.id is not None
    assert test_bottler.name == "Test Bottler"
    assert test_bottler.region_1 == "Region 1"
    assert test_bottler.region_2 == "Region 2"


def test_bottler_user_relationship(test_bottler, test_user):
    assert test_bottler.user == test_user
    assert test_user.bottlers[0] == test_bottler
