import copy
from unittest.mock import MagicMock, patch

from werkzeug.datastructures import MultiDict

from mywhiskies.extensions import db
from mywhiskies.forms.bottler import BottlerAddForm, BottlerEditForm
from mywhiskies.models import Bottler, User
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    list_bottlers,
)


def test_list_bottlers(test_user_01: User) -> None:
    result = list_bottlers(user=test_user_01, is_my_list=True)
    assert "bottlers" in result
    assert "total" in result
    assert "page" in result
    assert "per_page" in result
    assert "total_pages" in result
    assert result["total"] == len(test_user_01.bottlers)


def test_list_bottlers_search(test_user_01: User) -> None:
    first_bottler = test_user_01.bottlers[0]
    result = list_bottlers(user=test_user_01, is_my_list=True, q=first_bottler.name)
    assert result["total"] == 1
    assert result["bottlers"][0].name == first_bottler.name


def test_list_bottlers_sort(test_user_01: User) -> None:
    asc = list_bottlers(user=test_user_01, is_my_list=True, sort="name", direction="asc")
    desc = list_bottlers(user=test_user_01, is_my_list=True, sort="name", direction="desc")
    assert asc["bottlers"] == list(reversed(desc["bottlers"]))


@patch("mywhiskies.services.bottler.bottler.flash")
def test_add_bottler(mock_flash: MagicMock, test_user_01: User) -> None:
    form_data = MultiDict(
        {
            "name": "Crowded Barrel Whiskey",
            "region_1": "Austin",
            "region_2": "TX",
            "url": "https://www.crowdedbarrelwhiskey.com",
        }
    )
    form = BottlerAddForm(form_data)
    add_bottler(form, test_user_01)

    mock_flash.assert_called_once_with(
        '"Crowded Barrel Whiskey" has been successfully added.', "success"
    )


@patch("mywhiskies.services.bottler.bottler.flash")
def test_edit_bottler(mock_flash: MagicMock, test_bottler: Bottler) -> None:
    _bottler = db.get_or_404(Bottler, test_bottler.id)
    original_bottler = copy.deepcopy(_bottler.__dict__)

    form_data = MultiDict(
        {
            "name": "Single Cask Nation UPDATED",
            "region_1": "CT",
            "region_2": "USA",
            "url": "https://www.scn.com",
        }
    )
    form = BottlerEditForm(form_data)
    edit_bottler(form, test_bottler)
    mock_flash.assert_called_once_with(
        '"Single Cask Nation UPDATED" has been successfully updated.', "success"
    )

    assert original_bottler.get("name") != test_bottler.name
    assert original_bottler.get("region_1") != test_bottler.region_1
    assert original_bottler.get("region_2") != test_bottler.region_2
    assert original_bottler.get("url") != test_bottler.url


@patch("mywhiskies.services.bottler.bottler.flash")
def test_delete_bottler(
    mock_flash: MagicMock, test_user_01: User, test_bottler: Bottler
) -> None:
    delete_bottler(test_user_01, test_bottler)
    mock_flash.assert_called_once_with(
        '"Single Cask Nation" has been successfully deleted.', "success"
    )
