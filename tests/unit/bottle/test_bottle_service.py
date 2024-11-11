from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import request
from flask.testing import FlaskClient

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services.bottle.bottle import (
    add_bottle,
    delete_bottle,
    edit_bottle,
    list_bottles,
)


@pytest.fixture
def test_user(app):
    user = User(username="testuser", email="test@example.com")
    user.set_password("testPassword1234")
    db.session.add(user)
    db.session.commit()
    yield user
    # delete all bottles associated with the user before deleting the user
    bottles = (
        db.session.execute(db.select(Bottle).where(Bottle.user_id == user.id))
        .scalars()
        .all()
    )
    [db.session.delete(bottle) for bottle in bottles]
    db.session.commit()


@pytest.fixture
def test_bottle(app, test_user):
    bottle = Bottle(
        name="Test Bottle",
        type=BottleTypes.bourbon,
        abv=45.0,
        user_id=test_user.id,
    )
    db.session.add(bottle)
    db.session.commit()
    yield bottle
    # only attempt to delete if the bottle still exists
    if db.session.get(Bottle, bottle.id):
        db.session.delete(bottle)
        db.session.commit()


@patch("mywhiskies.services.bottle.bottle.render_template")
def test_list_bottles(mock_render_template, test_user, client: FlaskClient):
    mock_render_template.return_value = "Rendered Template"
    response = list_bottles(test_user, request, test_user)
    assert response.data == b"Rendered Template"


@patch("mywhiskies.services.bottle.bottle.add_bottle_images")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_add_bottle(mock_flash, mock_add_bottle_images, test_user):
    mock_add_bottle_images.return_value = True
    form = MagicMock(spec=BottleAddForm)
    form.distilleries.data = []
    form.bottler_id.data = "0"
    form.type.data = BottleTypes.bourbon
    form.name.data = "Test Bottle"
    form.abv.data = 45.0
    form.size.data = 750
    form.year_barrelled.data = 2020
    form.year_bottled.data = 2024
    form.url.data = "http://example.com"
    form.description.data = "A test bottle"
    form.review.data = "Great!"
    form.stars.data = 4.5
    form.cost.data = 50.0
    form.date_purchased.data = datetime(2024, 1, 1)
    form.date_opened.data = datetime(2024, 2, 1)
    form.date_killed.data = datetime(2024, 3, 1)
    add_bottle(form, test_user)
    mock_flash.assert_called_once_with(
        '"Test Bottle" has been successfully added.', "success"
    )


@patch("mywhiskies.services.bottle.bottle.edit_bottle_images")
@patch("mywhiskies.services.bottle.bottle.add_bottle_images")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_edit_bottle(
    mock_flash, mock_add_bottle_images, mock_edit_bottle_images, test_bottle
):
    mock_add_bottle_images.return_value = True
    form = MagicMock(spec=BottleEditForm)
    form.distilleries.data = []
    form.bottler_id.data = "0"
    form.type.data = BottleTypes.bourbon
    form.name.data = "Test Bottle"
    form.abv.data = 45.0
    form.size.data = 750
    form.year_barrelled.data = 2020
    form.year_bottled.data = 2024
    form.url.data = "http://example.com"
    form.description.data = "A test bottle"
    form.review.data = "Great!"
    form.stars.data = 4.5
    form.cost.data = 50.0
    form.date_purchased.data = datetime(2024, 1, 1)
    form.date_opened.data = datetime(2024, 2, 1)
    form.date_killed.data = datetime(2024, 3, 1)
    edit_bottle(form, test_bottle)
    mock_flash.assert_called_once_with(
        '"Test Bottle" has been successfully updated.', "success"
    )


@patch("mywhiskies.services.bottle.bottle.boto3.client")
@patch("mywhiskies.services.bottle.bottle.flash")
def test_delete_bottle(mock_flash, mock_boto_client, test_user, test_bottle):
    delete_bottle(test_user, test_bottle.id)
    mock_flash.assert_called_once_with("Bottle deleted successfully", "success")
