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
    # delete all bottles associated with the distillery before deleting the distillery
    if distillery.bottles:
        [db.session.delete(bottle) for bottle in distillery.bottles]
    # only attempt to delete if the distillery still exists
    if db.session.get(Distillery, distillery.id):
        db.session.delete(distillery)
        db.session.commit()
