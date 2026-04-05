from datetime import datetime
from unittest.mock import MagicMock, patch

from flask.testing import FlaskClient

from mywhiskies.forms.bottle import BottleAddForm, BottleEditForm
from mywhiskies.models import Bottle, BottleTypes, User
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    get_random_bottle,
    list_bottles_by_user,
    list_bottles_for_entity,
)


def test_list_bottles_returns_all(test_user_01: User) -> None:
    data = list_bottles_by_user(user=test_user_01, is_my_list=True)
    assert "bottles" in data
    assert "total" in data
    assert "has_killed" in data
    assert data["total"] == len(test_user_01.bottles)


def test_list_bottles_hides_private_for_guests(test_user_01: User) -> None:
    data = list_bottles_by_user(user=test_user_01, is_my_list=False)
    assert all(not b.is_private for b in data["bottles"])


def test_list_bottles_search(test_user_01: User) -> None:
    first_name = test_user_01.bottles[0].name.split()[0].lower()
    data = list_bottles_by_user(user=test_user_01, is_my_list=True, q=first_name)
    assert all(first_name in b.name.lower() for b in data["bottles"])


def test_list_bottles_type_filter(test_user_01: User) -> None:
    data = list_bottles_by_user(
        user=test_user_01, is_my_list=True, types=[BottleTypes.BOURBON.name]
    )
    assert all(b.type == BottleTypes.BOURBON for b in data["bottles"])


def test_list_bottles_pagination(test_user_01: User) -> None:
    data = list_bottles_by_user(user=test_user_01, is_my_list=True, per_page=1, page=1)
    assert len(data["bottles"]) == 1
    assert data["total_pages"] == data["total"]


def test_get_random_bottle(test_user_01: User) -> None:
    bottle = get_random_bottle(test_user_01)
    assert bottle is None or bottle in test_user_01.bottles


def test_list_bottles_for_entity_returns_dict(test_user_01: User) -> None:
    bottler = test_user_01.bottlers[0]
    data = list_bottles_for_entity(entity=bottler, is_my_list=True)
    assert "bottles" in data
    assert "total" in data
    assert "has_killed" in data
    assert data["total"] == len(bottler.bottles)


def test_list_bottles_for_entity_hides_private_for_guests(test_user_01: User) -> None:
    bottler = test_user_01.bottlers[0]
    data = list_bottles_for_entity(entity=bottler, is_my_list=False)
    assert all(not b.is_private for b in data["bottles"])


@patch("mywhiskies.services.bottle.bottle.add_bottle_images")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_add_bottle(
    mock_flash: MagicMock, mock_add_bottle_images: MagicMock, test_user_01: User
) -> None:
    mock_add_bottle_images.return_value = True
    form = MagicMock(spec=BottleAddForm)
    form.distilleries.data = [distillery.id for distillery in test_user_01.distilleries]
    form.bottler_id.data = "0"
    form.type.data = BottleTypes.BOURBON
    form.name.data = "Test Bottle"
    form.abv.data = 45.0
    form.size.data = 750
    form.year_barrelled.data = 2020
    form.year_bottled.data = 2024
    form.url.data = "http://example.com"
    form.description.data = "A test bottle"
    form.personal_note.data = "This one is in my nighstand for safe keeping."
    form.review.data = "Great!"
    form.stars.data = 4.5
    form.cost.data = 50.0
    form.date_purchased.data = datetime(2024, 1, 1)
    form.date_opened.data = datetime(2024, 2, 1)
    form.date_killed.data = datetime(2024, 3, 1)
    form.is_single_barrel.data = False
    form.is_private.data = False
    form.personal_note.data = None
    add_bottle(form, test_user_01)
    mock_flash.assert_called_once_with(
        '"Test Bottle" has been successfully added.', "success"
    )


@patch("mywhiskies.services.bottle.bottle.add_bottle_images")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_edit_bottle(
    mock_flash: MagicMock,
    mock_add_bottle_images: MagicMock,
    test_user_01: User,
    test_bottle: Bottle,
) -> None:
    mock_add_bottle_images.return_value = True
    form = MagicMock(spec=BottleEditForm)
    form.distilleries.data = [distillery.id for distillery in test_user_01.distilleries]
    form.bottler_id.data = "0"
    form.type.data = BottleTypes.BOURBON
    form.name.data = "Test Bottle"
    form.abv.data = 45.0
    form.size.data = 750
    form.year_barrelled.data = 2020
    form.year_bottled.data = 2024
    form.url.data = "http://example.com"
    form.description.data = "A test bottle"
    form.personal_note.data = "Moved to under the bed."
    form.review.data = "Great!"
    form.stars.data = 4.5
    form.cost.data = 50.0
    form.date_purchased.data = datetime(2024, 1, 1)
    form.date_opened.data = datetime(2024, 2, 1)
    form.date_killed.data = datetime(2024, 3, 1)
    form.is_single_barrel.data = False
    form.is_private.data = True
    form.personal_note.data = None
    edit_bottle(form, test_bottle)
    mock_flash.assert_called_once_with(
        '"Test Bottle" has been successfully updated.', "success"
    )


@patch("mywhiskies.services.bottle.bottle.boto3.client")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_delete_bottle(
    mock_flash: MagicMock,
    mock_boto_client: MagicMock,
    test_user_01: User,
    test_bottle: Bottle,
) -> None:
    delete_bottle(test_user_01, test_bottle)
    mock_flash.assert_called_once_with("Bottle deleted successfully", "success")
