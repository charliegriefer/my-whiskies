import copy
from datetime import datetime
from unittest.mock import MagicMock, patch

from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.distillery.forms import DistilleryEditForm, DistilleryForm
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.distillery.distillery import (
    add_distillery,
    delete_distillery,
    edit_distillery,
    get_distillery_detail,
    list_distilleries,
)


@patch("mywhiskies.services.utils.render_template")
def test_list_distilleries(
    mock_render_template: MagicMock, test_user_01: User, client: FlaskClient
) -> None:
    mock_render_template.return_value = "Rendered Template"
    request = MagicMock()
    response = list_distilleries(test_user_01, test_user_01, request, "distilleries")
    assert response.data == b"Rendered Template"


@patch("mywhiskies.services.distillery.distillery.flash")
def test_add_distillery(mock_flash: MagicMock, test_user_01: User) -> None:
    form_data = MultiDict(
        {
            "name": "Jack Daniel's",
            "description": (
                "Crafting something that endures for over 150 years takes time and character. "
                "You’ll find plenty of both in the people and history that make Jack Daniel’s."
            ),
            "region_1": "Lynchburg",
            "region_2": "TN",
            "url": "https://www.jackdaniels.com",
        }
    )
    form = DistilleryForm(form_data)
    add_distillery(form, test_user_01)

    mock_flash.assert_called_once_with(
        '"Jack Daniel\'s" has been successfully added.', "success"
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
        '"Jack Daniel\'s UPDATED" has been successfully updated.', "success"
    )

    assert original_distillery.get("name") != test_distillery.name
    assert original_distillery.get("region_1") != test_distillery.region_1
    assert original_distillery.get("region_2") != test_distillery.region_2
    assert original_distillery.get("url") != test_distillery.url


@patch("mywhiskies.services.distillery.distillery.flash")
def test_delete_distillery(
    mock_flash: MagicMock, test_user_01: User, test_distillery: Distillery
) -> None:
    delete_distillery(test_distillery.id, test_user_01)
    mock_flash.assert_called_once_with(
        '"Whiskey Del Bac" has been successfully deleted.', "success"
    )


@patch("mywhiskies.services.distillery.distillery.utils.is_my_list")
@patch("mywhiskies.services.distillery.distillery.db.get_or_404")
def test_get_distillery_detail(
    mock_get_or_404: MagicMock,
    mock_is_my_list: MagicMock,
    test_user_01: User,
    test_distillery: Distillery,
) -> None:
    # Mock setup
    test_distillery.user = test_user_01
    test_distillery.name = "Dry Fly Distilling"
    mock_get_or_404.return_value = test_distillery
    mock_is_my_list.return_value

    # Add bottles to distillery
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
    db.session.add_all([live_bottle, killed_bottle])
    db.session.commit()

    test_distillery.bottles = [live_bottle, killed_bottle]

    # simulate a GET request
    request = MagicMock(method="GET", cookies=MultiDict({"dt-list-length": "100"}))
    response = get_distillery_detail(test_distillery, request, test_user_01)
    html = response.get_data(as_text=True)

    # assertions for GET request
    expected_title = f"{test_distillery.user.username}&#39;s Whiskies: Distilleries: {test_distillery.name}"
    assert expected_title in html, f"Expected title '{expected_title}' not in HTML"
    assert "Live Bottle" in html
    assert "Killed Bottle" in html

    # simulate a POST request with "random_toggle" set to 1
    request = MagicMock(
        method="POST",
        cookies=MultiDict({"dt-list-length": "50"}),
        form=MultiDict({"random_toggle": "1", "bottle_type": ["bourbon"]}),
    )
    response = get_distillery_detail(test_distillery, request, test_user_01)

    # Parse the response HTML for POST
    html = response.get_data(as_text=True)

    # Assertions for the POST request
    assert (
        f"{test_distillery.user.username}&#39;s Whiskies: Distilleries: {test_distillery.name}"
        in html
    )
    assert "Live Bottle" in html
