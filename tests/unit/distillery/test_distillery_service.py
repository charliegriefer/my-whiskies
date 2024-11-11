from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
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


@pytest.fixture
def test_user(app: Flask) -> User:
    user = User(username="testuser", email="test@example.com")
    user.set_password("testPassword1234")
    db.session.add(user)
    db.session.commit()
    yield user
    # delete all distilleries associated with the user before deleting the user
    distilleries = (
        db.session.execute(db.select(Distillery).where(Distillery.user_id == user.id))
        .scalars()
        .all()
    )
    [db.session.delete(distillery) for distillery in distilleries]
    db.session.commit()


@pytest.fixture
def test_distillery(app: Flask, test_user: User) -> Distillery:
    distillery = Distillery(
        name="Frey Ranch",
        description="A ground-to-glass distillery in northern Nevada",
        region_1="Falon",
        region_2="MV",
        url="https://www.freyranch.edu",
        user_id=test_user.id,
    )
    db.session.add(distillery)
    db.session.commit()
    yield distillery
    # delete all bottles associated with the distillery before deleting the distllery
    distilleries = (
        db.session.execute(
            db.select(Distillery).where(Distillery.user_id == test_user.id)
        )
        .scalars()
        .all()
    )
    [db.session.delete(distillery) for distillery in distilleries]
    # only attempt to delete if the distillery still exists
    if db.session.get(Distillery, distillery.id):
        db.session.delete(distillery)
        db.session.commit()


@patch("mywhiskies.services.distillery.distillery.render_template")
def test_list_distilleries(
    mock_render_template: MagicMock, test_user: User, client: FlaskClient
) -> None:
    mock_render_template.return_value = "Rendered Template"
    response = list_distilleries(test_user, test_user)
    assert response.data == b"Rendered Template"


@patch("mywhiskies.services.distillery.distillery.flash")
def test_add_distillery(mock_flash: MagicMock, test_user: User) -> None:
    form_data = MultiDict(
        {
            "name": "Ironroot Republic",
            "region_1": "Denison",
            "region_2": "TX",
            "url": "https://www.ironrootrepublic.com",
        }
    )
    form = DistilleryForm(form_data)
    add_distillery(form, test_user)

    mock_flash.assert_called_once_with(
        '"Ironroot Republic" has been successfully added.', "success"
    )


@patch("mywhiskies.services.distillery.distillery.flash")
def test_edit_distillery(mock_flash: MagicMock, test_distillery: Distillery) -> None:
    original_distillery = db.get_or_404(Distillery, test_distillery.id)
    original_distillery_name = original_distillery.name
    original_distillery_region_1 = original_distillery.region_1
    original_distillery_region_2 = original_distillery.region_2
    original_distillery_url = original_distillery.url

    form_data = MultiDict(
        {
            "name": "Frey Ranch Farm and Distillery and Stuff",
            "region_1": "Fallon",
            "region_2": "NV",
            "url": "https://www.freyranch.com",
        }
    )
    form = DistilleryEditForm(form_data)
    edit_distillery(form, test_distillery)
    mock_flash.assert_called_once_with(
        '"Frey Ranch Farm and Distillery and Stuff" has been successfully updated.',
        "success",
    )

    assert original_distillery_name != test_distillery.name
    assert original_distillery_region_1 != test_distillery.region_1
    assert original_distillery_region_2 != test_distillery.region_2
    assert original_distillery_url != test_distillery.url


@patch("mywhiskies.services.distillery.distillery.flash")
def test_delete_distillery(
    mock_flash: MagicMock, test_user: User, test_distillery: Distillery
) -> None:
    delete_distillery(test_distillery.id, test_user)
    mock_flash.assert_called_once_with(
        '"Frey Ranch" has been successfully deleted.', "success"
    )


@patch("mywhiskies.services.distillery.distillery.utils.is_my_list")
@patch("mywhiskies.services.distillery.distillery.db.get_or_404")
def test_get_distillery_detail(
    mock_get_or_404: MagicMock,
    mock_is_my_list: MagicMock,
    test_user: User,
    test_distillery: Distillery,
) -> None:
    mock_get_or_404.return_value = test_distillery

    live_bottle = Bottle(
        name="Live Bottle",
        type=BottleTypes.bourbon,
        date_killed=None,
        user_id=test_user.id,
    )
    killed_bottle = Bottle(
        name="Killed Bottle",
        type=BottleTypes.bourbon,
        date_killed=datetime(2023, 1, 1),
        user_id=test_user.id,
    )
    test_distillery.bottles = [live_bottle, killed_bottle]
    mock_is_my_list.return_value = True

    # simulate a GET request
    request = MagicMock(method="GET", cookies=MultiDict({"dt-list-length": "100"}))
    context = get_distillery_detail(test_distillery.id, request, test_user)

    # assertions for GET request
    assert (
        context["title"]
        == f"{test_distillery.user.username}'s Whiskies: {test_distillery.name}"
    )
    assert context["bottles"] == test_distillery.bottles
    assert context["has_killed_bottles"] is True
    assert context["dt_list_length"] == "100"
    assert context["is_my_list"] is True

    # simulate a POST request with "random_toggle" set to 1
    request = MagicMock(
        method="POST",
        cookies=MultiDict({"dt-list-length": "50"}),
        form=MultiDict({"random_toggle": "1"}),
    )
    context = get_distillery_detail(test_distillery.id, request, test_user)

    # assertions for POST request
    assert "title" in context
    assert context["is_my_list"] is True
    assert len(context["bottles"]) <= 1  # only one bottle should be listed
    assert context["has_killed_bottles"] is False  # since we chose a live bottle only
    assert context["dt_list_length"] == "50"
