from decimal import Decimal

import pytest

from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.user.models import User


def test_bottle_creation(test_bottle: Bottle, test_user_01: User) -> None:
    assert test_bottle.id is not None
    assert test_bottle.name == "Four Roses Single Barrel"
    assert test_bottle.type == BottleTypes.BOURBON
    assert test_bottle.abv == pytest.approx(Decimal("56.10"), rel=1e-2)


def test_bottle_user_relationship(test_bottle: Bottle, test_user_01: User) -> None:
    assert test_bottle.user == test_user_01
    assert test_bottle in test_user_01.bottles
