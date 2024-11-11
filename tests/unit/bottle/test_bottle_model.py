import pytest

from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
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
def test_bottle(app, test_user):
    bottle = Bottle(
        name="Test Bottle",
        type=BottleTypes.bourbon,
        abv=45.0,
        user_id=test_user.id,
    )
    db.session.add(bottle)
    db.session.commit()
    yield bottle
    db.session.delete(bottle)
    db.session.commit()


def test_bottle_creation(test_bottle):
    assert test_bottle.id is not None
    assert test_bottle.name == "Test Bottle"
    assert test_bottle.type == BottleTypes.bourbon
    assert test_bottle.abv == 45.0


def test_bottle_user_relationship(test_bottle, test_user):
    assert test_bottle.user == test_user
    assert test_user.bottles[0] == test_bottle
