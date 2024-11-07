from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User
from tests.conftest import expected_page_title


def test_distillery_list(client: FlaskClient, test_user: User):
    expected_title = expected_page_title(test_user.username)

    response = client.get(
        url_for("distillery.distilleries_list", username=test_user.username)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200

    assert expected_title in response_data
    for distillery in test_user.distilleries:
        assert distillery.name in response_data
        assert distillery.region_1 in response_data
        if distillery.url:
            assert distillery.url in response_data


def distillery_list_logged_in_elements(
    logged_in_user: FlaskClient, test_user: User, npc_user: User
):
    client = logged_in_user

    # get the distillery list page for another user.
    # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
    response = client.get(
        url_for("distillery.distilleries_list", username=npc_user.username)
    )
    assert response.status_code == 200

    response_data = response.get_data(as_text=True)

    assert "Add Distillery" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    # get the distillery  list page the current user.
    # now we should see the edit and delete iconss, as well as the "Add" button.
    response = client.get(
        url_for("distillery.distilleries_list", username=test_user.username)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200

    assert "Add Distillery" in response_data
    assert "bi-pencil" in response_data
    assert "bi-trash" in response_data


def test_distillery_list_logged_out_elements(client: FlaskClient):
    # not logged in, so we shouldn't see the add bottler button, or any edit or delete icons in any lists.
    response = client.get(url_for("distillery.distilleries_list", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Add Distillery" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    response = client.get(url_for("distillery.distilleries_list", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Add Distillery" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data
