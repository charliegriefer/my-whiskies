from flask import Flask, url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_USER_PASSWORD, html_encode


def test_bottler_list(client: FlaskClient, test_user: User):

    suffix = "'s" if not test_user.username.endswith("s") else "'"
    expected_title = html_encode(f"{test_user.username}{suffix} Whiskies")

    response = client.get(url_for("bottler.bottlers_list", username=test_user.username))
    assert response.status_code == 200
    response_data = response.get_data(as_text=True)

    assert expected_title in response_data
    for bottler in test_user.bottlers:
        assert bottler.name in response_data
        assert bottler.region_1 in response_data
        if bottler.url:
            assert bottler.url in response_data


def test_bottler_list_logged_in_elements(
    app: Flask, client: FlaskClient, test_user: User, npc_user: User
):
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user.username,
            "password": TEST_USER_PASSWORD,
        },
    )

    # get the bottler list page for another user.
    # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
    response = client.get(url_for("bottler.bottlers_list", username=npc_user.username))
    assert response.status_code == 200

    response_data = response.get_data(as_text=True)

    assert "Add Bottler" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    # get the bottler list page the current user.
    # now we should see the edit and delete iconss, as well as the "Add" button.
    response = client.get(url_for("bottler.bottlers_list", username=test_user.username))
    assert response.status_code == 200

    response_data = response.get_data(as_text=True)

    assert "Add Bottler" in response_data
    assert "bi-pencil" in response_data
    assert "bi-trash" in response_data


def test_bottler_list_logged_out_elements(app: Flask):
    with app.test_client() as client:
        # not logged in, so we shouldn't see the add bottler button, or any edit or delete icons in any lists.
        response = client.get(url_for("bottler.bottlers_list", username="testuser"))
        response_data = response.get_data(as_text=True)
        assert "Add Bottler" not in response_data
        assert "bi-pencil" not in response_data
        assert "bi-trash" not in response_data

        response = client.get(url_for("bottler.bottlers_list", username="testuser"))
        response_data = response.get_data(as_text=True)
        assert "Add Bottler" not in response_data
        assert "bi-pencil" not in response_data
        assert "bi-trash" not in response_data
