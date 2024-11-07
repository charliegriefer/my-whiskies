from flask import Flask, url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_USER_PASSWORD, html_encode


def test_bottle_list(app: Flask, client: FlaskClient, test_user: User) -> None:
    response = client.get(url_for("bottle.list_bottles", username=test_user.username))

    assert response.status_code == 200

    suffix = "'s" if not test_user.username.endswith("s") else "'"
    expected_title = html_encode(f"{test_user.username}{suffix} Whiskies")

    response_data = response.get_data(as_text=True)

    assert expected_title in response_data
    for bottle in test_user.bottles:
        assert bottle.name in response_data
        assert bottle.type.name in response_data
        if bottle.abv:
            assert str(bottle.abv) in response_data
        assert bottle.description in response_data


def test_bottle_list_logged_in_elements(
    app: Flask,
    client: FlaskClient,
    test_user: User,
    npc_user: User,
) -> None:
    # log in the test user
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user.username,
            "password": TEST_USER_PASSWORD,
        },
    )

    # get the bottle list page for another user.
    # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
    response = client.get(url_for("bottle.list_bottles", username=npc_user.username))
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Random Bottle" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    # get the bottle list page the current user.
    # now we should see the edit and delete iconss, as well as the "random" button.
    response = client.get(url_for("bottle.list_bottles", username=test_user.username))
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Random Bottle" in response_data
    assert "bi-pencil" in response_data
    assert "bi-trash" in response_data


def test_bottle_list_logged_out_elements(app: Flask, client: FlaskClient) -> None:
    # not logged in, so we shouldn't see the random bottle button, or any edit or delete icons in any lists.
    response = client.get(url_for("bottle.list_bottles", username="testuser"))
    assert b"Random Bottle" not in response.data
    assert b"bi-pencil" not in response.data
    assert b"bi-trash" not in response.data

    response = client.get(url_for("bottle.list_bottles", username="testuser"))
    assert b"Random Bottle" not in response.data
    assert b"bi-pencil" not in response.data
    assert b"bi-trash" not in response.data
