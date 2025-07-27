import pytest
from flask import Flask
from mywhiskies.extensions import db
from mywhiskies.models import Bottle, BottleTypes, User


@pytest.fixture
def test_bottle(app: Flask, test_user_01: User) -> Bottle:
    bottle = Bottle(
        name="Four Roses Single Barrel",
        type=BottleTypes.BOURBON,
        abv=56.10,
        user_id=test_user_01.id,
    )
    db.session.add(bottle)
    db.session.commit()
    yield bottle
    if db.session.get(Bottle, bottle.id):
        db.session.delete(bottle)
        db.session.commit()
