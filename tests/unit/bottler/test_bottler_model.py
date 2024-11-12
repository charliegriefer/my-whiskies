from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User


def test_bottler_creation(test_bottler: Bottler) -> None:
    assert test_bottler.id is not None
    assert test_bottler.name == "Single Cask Nation"
    assert test_bottler.region_1 == "Guilford"
    assert test_bottler.region_2 == "CT"


def test_bottler_user_relationship(test_bottler: Bottler, test_user_01: User) -> None:
    assert test_bottler.user == test_user_01
    assert test_bottler in test_user_01.bottlers
