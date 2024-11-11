import pytest

from mywhiskies.blueprints.distillery.models import Distillery
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
def test_distillery(app, test_user):
    distillery = Distillery(
        name="Test Distillery",
        region_1="Region 1",
        region_2="Region 2",
        user_id=test_user.id,
    )
    db.session.add(distillery)
    db.session.commit()
    yield distillery
    db.session.delete(distillery)
    db.session.commit()


def test_distillery_creation(test_distillery):
    assert test_distillery.id is not None
    assert test_distillery.name == "Test Distillery"
    assert test_distillery.region_1 == "Region 1"
    assert test_distillery.region_2 == "Region 2"


def test_distillery_user_relationship(test_distillery, test_user):
    assert test_distillery.user == test_user
    assert test_user.distilleries[0] == test_distillery
