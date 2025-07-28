import pytest
from flask import Flask
from mywhiskies.extensions import db
from mywhiskies.models import Bottler, User


@pytest.fixture
def test_bottler(app: Flask, test_user_01: User) -> Bottler:
    bottler = Bottler(
        name="Single Cask Nation",
        description="Bottled by whisky geeks for whisky geeks the world over.",
        region_1="Guilford",
        region_2="CT",
        url="https://www.singlecasknation.com",
        user_id=test_user_01.id,
    )
    db.session.add(bottler)
    db.session.commit()

    yield bottler

    # check if bottles are still associated with the bottler and delete if present
    for bottle in bottler.bottles:
        # ensure that the bottle has a non-null primary key before attempting to get it
        if bottle.id is not None and db.session.get(type(bottle), bottle.id):
            db.session.delete(bottle)

    # only attempt to delete if the bottler still exists
    if db.session.get(Bottler, bottler.id):
        db.session.delete(bottler)

    db.session.commit()
