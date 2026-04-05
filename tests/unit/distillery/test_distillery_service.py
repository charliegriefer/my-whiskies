import copy
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import MultiDict

from mywhiskies.extensions import db
from mywhiskies.forms.distillery import DistilleryAddForm, DistilleryEditForm
from mywhiskies.models import Distillery, User
from mywhiskies.services.distillery.distillery import (
    add_distillery,
    delete_distillery,
    edit_distillery,
    list_distilleries,
)


def test_list_distilleries(test_user_01: User) -> None:
    result = list_distilleries(user=test_user_01, is_my_list=True)
    assert "distilleries" in result
    assert "total" in result
    assert "page" in result
    assert "per_page" in result
    assert "total_pages" in result
    assert result["total"] == len(test_user_01.distilleries)


def test_list_distilleries_search(test_user_01: User) -> None:
    first = test_user_01.distilleries[0]
    result = list_distilleries(user=test_user_01, is_my_list=True, q=first.name)
    assert result["total"] == 1
    assert result["distilleries"][0].name == first.name


def test_list_distilleries_sort(test_user_01: User) -> None:
    asc = list_distilleries(user=test_user_01, is_my_list=True, sort="name", direction="asc")
    desc = list_distilleries(user=test_user_01, is_my_list=True, sort="name", direction="desc")
    assert asc["distilleries"] == list(reversed(desc["distilleries"]))


@patch("mywhiskies.services.distillery.distillery.flash")
def test_add_distillery(mock_flash: MagicMock, test_user_01: User) -> None:
    form_data = MultiDict(
        {
            "name": "Jack Daniel's",
            "description": (
                "Crafting something that endures for over 150 years takes time and character. "
                "You'll find plenty of both in the people and history that make Jack Daniel's."
            ),
            "region_1": "Lynchburg",
            "region_2": "TN",
            "url": "https://www.jackdaniels.com",
        }
    )
    form = DistilleryAddForm(form_data)
    add_distillery(form, test_user_01)

    mock_flash.assert_called_once_with(
        'Distillery "Jack Daniel\'s" has been successfully added.', "success"
    )


@patch("mywhiskies.services.distillery.distillery.flash")
def test_edit_distillery(mock_flash: MagicMock, test_distillery: Distillery) -> None:
    _distillery = db.get_or_404(Distillery, test_distillery.id)
    original_distillery = copy.deepcopy(_distillery.__dict__)

    form_data = MultiDict(
        {
            "name": "Jack Daniel's UPDATED",
            "region_1": "Lynchburger",
            "region_2": "TX",
            "url": "https://www.jackdaniels.org",
        }
    )
    form = DistilleryEditForm(form_data)
    edit_distillery(form, test_distillery)
    mock_flash.assert_called_once_with(
        'Distillery "Jack Daniel\'s UPDATED" has been successfully updated.', "success"
    )

    assert original_distillery.get("name") != test_distillery.name
    assert original_distillery.get("region_1") != test_distillery.region_1
    assert original_distillery.get("region_2") != test_distillery.region_2
    assert original_distillery.get("url") != test_distillery.url


@patch("mywhiskies.services.distillery.distillery.flash")
def test_delete_distillery(
    mock_flash: MagicMock, test_user_01: User, test_distillery: Distillery
) -> None:
    delete_distillery(test_user_01, test_distillery)
    mock_flash.assert_called_once_with(
        'Distillery "Whiskey Del Bac" has been successfully deleted.', "success"
    )
