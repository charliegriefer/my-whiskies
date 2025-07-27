from datetime import datetime
from unittest.mock import MagicMock, patch

from flask import request
from flask.testing import FlaskClient
from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.models import Bottle, BottleTypes, User
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    list_bottles_by_user,
)


@patch("mywhiskies.services.utils.render_template")
def test_list_bottles(
    mock_render_template: MagicMock, test_user_01: User, client: FlaskClient
) -> None:
    mock_render_template.return_value = "Rendered Template"
    response = list_bottles_by_user(test_user_01, request, test_user_01)
    assert response.data == b"Rendered Template"


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
    delete_bottle(test_user_01, test_bottle.id)
    mock_flash.assert_called_once_with("Bottle deleted successfully", "success")
