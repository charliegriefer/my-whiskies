import copy
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.bottler.forms import BottlerAddForm, BottlerEditForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottler.bottler import (
    add_bottler,
    delete_bottler,
    edit_bottler,
    get_bottler_detail,
    list_bottlers,
)


@patch("mywhiskies.services.bottler.bottler.render_template")
def test_list_bottlers(
    mock_render_template: MagicMock, test_user_01: User, client: FlaskClient
) -> None:
    mock_render_template.return_value = "Rendered Template"
    response = list_bottlers(test_user_01, test_user_01)
    assert response.data == b"Rendered Template"


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
    delete_bottler(test_user_01, test_bottler.id)
    mock_flash.assert_called_once_with(
        '"Single Cask Nation" has been successfully deleted.', "success"
    )


@patch("mywhiskies.services.bottler.bottler.utils.is_my_list")
@patch("mywhiskies.services.bottler.bottler.db.get_or_404")
def test_get_bottler_detail(
    mock_get_or_404: MagicMock,
    mock_is_my_list: MagicMock,
    test_user_01: User,
    test_bottler: Bottler,
) -> None:
    mock_get_or_404.return_value = test_bottler

    live_bottle = Bottle(
        name="Live Bottle",
        type=BottleTypes.bourbon,
        date_killed=None,
        user_id=test_user_01.id,
    )
    killed_bottle = Bottle(
        name="Killed Bottle",
        type=BottleTypes.bourbon,
        date_killed=datetime(2023, 1, 1),
        user_id=test_user_01.id,
    )
    test_bottler.bottles = [live_bottle, killed_bottle]
    mock_is_my_list.return_value = True

    # simulate a GET request
    request = MagicMock(method="GET", cookies=MultiDict({"dt-list-length": "100"}))
    context = get_bottler_detail(test_bottler.id, request, test_user_01)

    # assertions for GET request
    assert (
        context["title"]
        == f"{test_bottler.user.username}'s Whiskies: {test_bottler.name}"
    )
    assert context["bottles"] == test_bottler.bottles
    assert context["has_killed_bottles"] is True
    assert context["dt_list_length"] == "100"
    assert context["is_my_list"] is True

    # simulate a POST request with "random_toggle" set to 1
    request = MagicMock(
        method="POST",
        cookies=MultiDict({"dt-list-length": "50"}),
        form=MultiDict({"random_toggle": "1"}),
    )
    context = get_bottler_detail(test_bottler.id, request, test_user_01)

    # assertions for POST request
    assert "title" in context
    assert context["is_my_list"] is True
    assert len(context["bottles"]) <= 1  # only one bottle should be listed
    assert context["has_killed_bottles"] is False  # since we chose a live bottle only
    assert context["dt_list_length"] == "50"
