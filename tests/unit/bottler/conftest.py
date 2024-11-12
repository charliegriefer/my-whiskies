import pytest
from flask import Flask

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_bottler(app: Flask, test_user: User) -> Bottler:
    bottler = Bottler(
        name="Single Cask Nation",
        description="Bottled by whisky geeks for whisky geeks the world over.",
        region_1="Guilford",
        region_2="CT",
        url="https://www.singlecasknation.com",
        user_id=test_user.id,
    )
    db.session.add(bottler)
    db.session.commit()
    yield bottler
    # delete all bottles associated with the bottler before deleting the bottler
    bottlers = (
        db.session.execute(db.select(Bottler).where(Bottler.user_id == test_user.id))
        .scalars()
        .all()
    )
    [db.session.delete(bottler) for bottler in bottlers]
    # only attempt to delete if the bottler still exists
    if db.session.get(Bottler, bottler.id):
        db.session.delete(bottler)
        db.session.commit()
