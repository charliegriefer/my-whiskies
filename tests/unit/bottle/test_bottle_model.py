from decimal import Decimal

import pytest
from mywhiskies.extensions import db
from mywhiskies.models import Bottle, BottleTypes, User


def test_bottle_creation(test_bottle: Bottle, test_user_01: User) -> None:
    assert test_bottle.id is not None
    assert test_bottle.name == "Four Roses Single Barrel"
    assert test_bottle.type == BottleTypes.BOURBON
    assert test_bottle.abv == pytest.approx(Decimal("56.10"), rel=1e-2)


def test_bottle_user_relationship(test_bottle: Bottle, test_user_01: User) -> None:
    assert test_bottle.user == test_user_01
    assert test_bottle in test_user_01.bottles


# --- before_insert event: user_num auto-increment ---

def test_user_num_assigned_on_insert(test_user_01: User) -> None:
    bottle = Bottle(name="New Bottle", type=BottleTypes.RYE, user_id=test_user_01.id)
    db.session.add(bottle)
    db.session.commit()
    assert bottle.user_num is not None
    assert bottle.user_num > 0


def test_user_num_increments_sequentially(test_user_01: User) -> None:
    before = max(b.user_num for b in test_user_01.bottles)
    bottle = Bottle(name="Sequential Bottle", type=BottleTypes.RYE, user_id=test_user_01.id)
    db.session.add(bottle)
    db.session.commit()
    assert bottle.user_num == before + 1


# --- before_insert / before_update event: clean_bottle_data ---

def test_clean_bottle_data_strips_name_whitespace(test_user_01: User) -> None:
    bottle = Bottle(name="  Padded Name  ", type=BottleTypes.BOURBON, user_id=test_user_01.id)
    db.session.add(bottle)
    db.session.commit()
    assert bottle.name == "Padded Name"


def test_clean_bottle_data_converts_empty_url_to_none(test_user_01: User) -> None:
    bottle = Bottle(
        name="No URL Bottle", type=BottleTypes.BOURBON, user_id=test_user_01.id, url=""
    )
    db.session.add(bottle)
    db.session.commit()
    assert bottle.url is None


def test_clean_bottle_data_on_update(test_bottle: Bottle) -> None:
    test_bottle.name = "  Updated With Spaces  "
    test_bottle.url = ""
    db.session.commit()
    assert test_bottle.name == "Updated With Spaces"
    assert test_bottle.url is None
