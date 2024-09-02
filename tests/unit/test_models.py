import datetime

import pytest

from app.extensions import db
from app.models import Bottle, Bottler, Distillery, User


pw = "LuCwH6jOZk"

test_user_username = "whiskeytest1725"
test_user_email = "whiskeytest@griefer.com"

test_distillery_1 = {
    "name": "Test Distillery 1",
    "region_1": "Fallon",
    "region_2": "NV"
}
test_distillery_2 = {
    "name": "Test Distillery 2",
    "region_1": "Denisonx",
    "region_2": "TX"
}

test_bottler = {
    "name": "Test Bottler",
    "region_1": "Vergennes",
    "region_2": "VT"
}


def test_user_add(client):
    user = User(username=test_user_username, email=test_user_email)
    user.set_password(pw)
    assert user.id is None

    db.session.add(user)
    db.session.commit()

    assert user.username == test_user_username
    assert user.email == test_user_email
    assert not user.email_confirmed
    assert not user.is_deleted
    assert user.id is not None
    assert user.date_registered.date() == datetime.datetime.utcnow().date()

    db.session.delete(user)
    db.session.commit()


def test_user_add_dupe_username(client):
    user_1 = User(username=test_user_username, email=test_user_email)
    user_1.set_password(pw)

    user_2 = User(username=test_user_username, email="xxx@griefer.com")
    user_2.set_password(pw)

    db.session.add(user_1)
    db.session.commit()

    with pytest.raises(Exception) as e:
        db.session.add(user_2)
        db.session.commit()

    assert f"Duplicate entry '{test_user_username}' for key" in str(e.value)
    db.session.rollback()
    db.session.delete(user_1)
    db.session.commit()


def test_user_add_dupe_email(client):
    user_1 = User(username=test_user_username, email=test_user_email)
    user_1.set_password(pw)

    user_2 = User(username="whiskeytest1726", email=test_user_email)
    user_2.set_password(pw)

    db.session.add(user_1)
    db.session.commit()

    with pytest.raises(Exception) as e:
        db.session.add(user_2)
        db.session.commit()

    assert f"Duplicate entry '{test_user_email}' for key" in str(e.value)
    db.session.rollback()
    db.session.delete(user_1)
    db.session.commit()


def test_add_distillery(client):
    user = User(username=test_user_username, email=test_user_email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()

    assert not user.distilleries  # user should have no distilleries as of yet.

    distillery_1 = Distillery(**test_distillery_1, user_id=user.id)
    db.session.add(distillery_1)
    db.session.commit()

    assert distillery_1.id is not None
    assert distillery_1.name == test_distillery_1.get("name")
    assert distillery_1.region_1 == test_distillery_1.get("region_1")
    assert distillery_1.region_2 == test_distillery_1.get("region_2")

    assert len(user.distilleries) == 1

    distillery_2 = Distillery(**test_distillery_2, user_id=user.id)
    db.session.add(distillery_2)
    db.session.commit()

    assert len(user.distilleries) == 2

    db.session.delete(distillery_2)
    db.session.delete(distillery_1)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()


def test_add_bottler(client):
    user = User(username=test_user_username, email=test_user_email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()

    assert not user.bottlers  # user should have no bottlers as of yet.

    bottler = Bottler(**test_bottler, user_id=user.id)
    db.session.add(bottler)
    db.session.commit()

    assert len(user.bottlers) == 1

    db.session.delete(bottler)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()


def test_add_bottle(client):
    user = User(username=test_user_username, email=test_user_email)
    user.set_password(pw)
    db.session.add(user)
    db.session.commit()

    assert not user.bottles  # user should have no bottles as of yet.

    distillery = Distillery(**test_distillery_1, user_id=user.id)
    db.session.add(distillery)
    db.session.commit()

    bottle = Bottle(name="Test Bottle", user_id=user.id, type="bourbon", distilleries=[distillery])
    db.session.add(bottle)
    db.session.commit()

    assert bottle.id is not None
    assert bottle.name == "Test Bottle"
    assert len(bottle.distilleries) == 1
    assert bottle.distilleries[0].name == test_distillery_1.get("name")
    assert len(user.bottles) == 1

    db.session.delete(bottle)
    db.session.commit()
    db.session.delete(distillery)
    db.session.commit()
    db.session.delete(user)
    db.session.commit()
