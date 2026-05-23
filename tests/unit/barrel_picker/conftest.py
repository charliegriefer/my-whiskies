import pytest
from flask import Flask

from mywhiskies.extensions import db
from mywhiskies.models import BarrelPicker, User


@pytest.fixture
def test_barrel_picker(app: Flask, test_user_01: User) -> BarrelPicker:
    picker = BarrelPicker(
        name="Total Beverage Solution",
        description="Colorado-based single barrel picker.",
        url="https://www.totalbev.com",
        user_id=test_user_01.id,
    )
    db.session.add(picker)
    db.session.commit()

    yield picker

    if db.session.get(BarrelPicker, picker.id):
        db.session.delete(picker)
    db.session.commit()
