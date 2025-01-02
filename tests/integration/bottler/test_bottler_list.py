from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User
from tests.conftest import expected_page_title


def test_bottler_list(client: FlaskClient, test_user_01: User):
    expected_title = expected_page_title(test_user_01.username)

    response = client.get(
        url_for("bottler.bottler_list", username=test_user_01.username)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200

    assert expected_title in response_data
    for bottler in test_user_01.bottlers:
        assert bottler.name in response_data
        assert bottler.region_1 in response_data
        if bottler.url:
            assert bottler.url in response_data


def test_bottler_list_logged_in_elements(
    logged_in_user_01: FlaskClient, test_user_01: User, test_user_02: User
):
    client = logged_in_user_01

    # get the bottler list page for another user.
    # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
    response = client.get(
        url_for("bottler.bottler_list", username=test_user_02.username)
    )
    assert response.status_code == 200

    response_data = response.get_data(as_text=True)

    # looking for the "Add Bottler" button
    assert (
        f'<a class="btn btn-primary" href="/{test_user_02.username}/bottler/add"'
        not in response_data
    )
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    # get the bottler list page the current user.
    # now we should see the edit and delete iconss, as well as the "Add" button.
    response = client.get(
        url_for("bottler.bottler_list", username=test_user_01.username)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200

    # looking for the "Add Bottler" button

    assert (
        f'<a class="btn btn-primary" href="/{test_user_01.username}/bottler/add"'
        in response_data
    )
    assert "bi-pencil" in response_data
    assert "bi-trash" in response_data


def test_bottler_list_logged_out_elements(client: FlaskClient):
    # not logged in, so we shouldn't see the add bottler button, or any edit or delete icons in any lists.
    response = client.get(url_for("bottler.bottler_list", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Add Bottler" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    response = client.get(url_for("bottler.bottler_list", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Add Bottler" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data
