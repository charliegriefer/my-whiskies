from mywhiskies.extensions import db
from mywhiskies.models import BarrelPicker, User


def test_barrel_picker_creation(test_barrel_picker: BarrelPicker) -> None:
    assert test_barrel_picker.id is not None
    assert test_barrel_picker.name == "Total Beverage Solution"
    assert test_barrel_picker.url == "https://www.totalbev.com"


def test_barrel_picker_user_num_assigned(test_barrel_picker: BarrelPicker) -> None:
    assert test_barrel_picker.user_num is not None
    assert test_barrel_picker.user_num >= 1


def test_barrel_picker_user_relationship(test_barrel_picker: BarrelPicker, test_user_01: User) -> None:
    assert test_barrel_picker.user == test_user_01
    assert test_barrel_picker in test_user_01.barrel_pickers


def test_barrel_picker_user_num_increments(test_barrel_picker: BarrelPicker, test_user_01: User) -> None:
    second = BarrelPicker(name="Second Picker", user_id=test_user_01.id)
    db.session.add(second)
    db.session.commit()
    assert second.user_num == test_barrel_picker.user_num + 1
