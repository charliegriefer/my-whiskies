from mywhiskies.models import Distillery, User


def test_distillery_creation(test_distillery: Distillery) -> None:
    assert test_distillery.id is not None
    assert test_distillery.name == "Whiskey Del Bac"
    assert test_distillery.description == (
        "Every whiskey from Whiskey Del Bac is handcrafted, non-sourced, "
        "aged in the desert and bottled in Tucson, Arizona with a love of whiskey and the desert."
    )
    assert test_distillery.region_1 == "Tucson"
    assert test_distillery.region_2 == "AZ"


def test_distillery_user_relationship(
    test_distillery: Distillery, test_user_01: User
) -> None:
    assert test_distillery.user == test_user_01
    assert test_distillery in test_user_01.distilleries
