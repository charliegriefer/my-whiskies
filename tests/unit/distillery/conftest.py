import pytest
from flask import Flask

from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db


@pytest.fixture
def test_distillery(app: Flask, test_user_01: User) -> Distillery:
    distillery = Distillery(
        name="Whiskey Del Bac",
        description=(
            "Every whiskey from Whiskey Del Bac is handcrafted, non-sourced, "
            "aged in the desert and bottled in Tucson, Arizona with a love of whiskey and the desert."
        ),
        region_1="Tucson",
        region_2="AZ",
        url="https://www.whiskeydelbac.com/",
        user_id=test_user_01.id,
    )
    db.session.add(distillery)
    db.session.commit()

    yield distillery

    # check if bottles are still associated with the distillery and delete if present
    for bottle in distillery.bottles:
        # ensure that the bottle has a non-null primary key before attempting to get it
        if bottle.id is not None and db.session.get(type(bottle), bottle.id):
            db.session.delete(bottle)

    # only attempt to delete if the distillery still exists
    if db.session.get(Distillery, distillery.id):
        db.session.delete(distillery)

    db.session.commit()
