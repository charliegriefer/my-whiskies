from flask import Flask, url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User
from tests.conftest import expected_page_title


def test_bottle_list(client: FlaskClient, test_user: User) -> None:
    expected_title = expected_page_title(test_user.username)

    response = client.get(url_for("bottle.list_bottles", username=test_user.username))
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200

    assert expected_title in response_data
    for bottle in test_user.bottles:
        assert bottle.name in response_data
        assert bottle.type.name in response_data
        if bottle.abv:
            assert str(bottle.abv) in response_data
        assert bottle.description in response_data


def test_bottle_list_logged_in_elements(
    logged_in_user: FlaskClient, test_user: User, npc_user: User
) -> None:

    # get the bottle list page for another user.
    # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
    response = logged_in_user.get(
        url_for("bottle.list_bottles", username=npc_user.username)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Random Bottle" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    # get the bottle list page the current user.
    # now we should see the edit and delete iconss, as well as the "random" button.
    response = logged_in_user.get(
        url_for("bottle.list_bottles", username=test_user.username)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Random Bottle" in response_data
    assert "bi-pencil" in response_data
    assert "bi-trash" in response_data


def test_bottle_list_logged_out_elements(app: Flask, client: FlaskClient) -> None:
    # not logged in, so we shouldn't see the random bottle button, or any edit or delete icons in any lists.
    response = client.get(url_for("bottle.list_bottles", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Random Bottle" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data

    response = client.get(url_for("bottle.list_bottles", username="testuser"))
    response_data = response.get_data(as_text=True)
    assert "Random Bottle" not in response_data
    assert "bi-pencil" not in response_data
    assert "bi-trash" not in response_data
