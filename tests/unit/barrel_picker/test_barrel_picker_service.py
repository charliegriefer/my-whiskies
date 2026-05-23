from werkzeug.datastructures import MultiDict

from mywhiskies.extensions import db
from mywhiskies.forms.barrel_picker import BarrelPickerAddForm, BarrelPickerEditForm
from mywhiskies.models import BarrelPicker, User
from mywhiskies.services.barrel_picker.barrel_picker import (
    add_barrel_picker,
    delete_barrel_picker,
    edit_barrel_picker,
)


def test_add_barrel_picker(test_user_01: User) -> None:
    form = BarrelPickerAddForm(MultiDict({"name": "K&L Wine Merchants", "url": "https://www.klwines.com"}))
    picker = add_barrel_picker(form, test_user_01)
    assert picker.name == "K&L Wine Merchants"
    assert picker.user == test_user_01
    assert picker.id is not None


def test_add_barrel_picker_increments_user_num(test_user_01: User, test_barrel_picker: BarrelPicker) -> None:
    form = BarrelPickerAddForm(MultiDict({"name": "Second Picker"}))
    second = add_barrel_picker(form, test_user_01)
    assert second.user_num == test_barrel_picker.user_num + 1


def test_edit_barrel_picker(test_barrel_picker: BarrelPicker) -> None:
    form = BarrelPickerEditForm(MultiDict({"name": "Total Bev UPDATED", "url": "https://www.totalbev.com"}))
    edit_barrel_picker(form, test_barrel_picker)
    assert test_barrel_picker.name == "Total Bev UPDATED"


def test_edit_barrel_picker_updates_fields(test_barrel_picker: BarrelPicker) -> None:
    original_name = test_barrel_picker.name
    form = BarrelPickerEditForm(
        MultiDict({"name": "New Name", "description": "New description", "url": "https://example.com"})
    )
    edit_barrel_picker(form, test_barrel_picker)
    assert test_barrel_picker.name != original_name
    assert test_barrel_picker.description == "New description"


def test_delete_barrel_picker(test_user_01: User, test_barrel_picker: BarrelPicker) -> None:
    picker_id = test_barrel_picker.id
    ok, message = delete_barrel_picker(test_user_01, test_barrel_picker)
    assert ok is True
    assert "Total Beverage Solution" in message
    assert "successfully deleted" in message
    assert db.session.get(BarrelPicker, picker_id) is None


def test_delete_barrel_picker_wrong_user(test_user_02: User, test_barrel_picker: BarrelPicker) -> None:
    ok, message = delete_barrel_picker(test_user_02, test_barrel_picker)
    assert ok is False
    assert "Permission denied" in message


def test_delete_barrel_picker_clears_bottle_associations(
    test_user_01: User, test_barrel_picker: BarrelPicker
) -> None:
    bottle = test_user_01.bottles[0]
    test_barrel_picker.bottles = [bottle]
    db.session.commit()
    assert len(test_barrel_picker.bottles) == 1

    ok, _ = delete_barrel_picker(test_user_01, test_barrel_picker)
    assert ok is True
    db.session.refresh(bottle)
    assert bottle.id is not None
