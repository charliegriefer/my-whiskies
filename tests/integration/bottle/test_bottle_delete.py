from flask import Flask, url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_USER_PASSWORD


def test_delete_bottle_not_logged_in(
    app: Flask,
    client: FlaskClient,
    test_user_bottle_to_delete: Bottle,
) -> None:
    """Test that a user must be logged in to delete a bottle."""
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=test_user_bottle_to_delete.id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_bottle(
    app: Flask, client: FlaskClient, test_user: User, npc_user: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's bottle."""
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user.username,
            "password": TEST_USER_PASSWORD,
        },
    )
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=npc_user.bottles[0].id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "There was an issue deleting this bottle" in response.get_data(as_text=True)


def test_delete_my_bottle(
    app: Flask,
    client: FlaskClient,
    test_user: User,
    test_user_bottle_to_delete: Bottle,
) -> None:
    client.post(
        url_for("auth.login"),
        data={
            "username": test_user.username,
            "password": TEST_USER_PASSWORD,
        },
    )
    bottles_before_delete = [bottle.name for bottle in test_user.bottles]

    # Perform the delete operation
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=test_user_bottle_to_delete.id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bottle deleted successfully" in response.get_data(as_text=True)

    bottles_after_delete = [bottle.name for bottle in test_user.bottles]

    assert len(bottles_after_delete) == len(bottles_before_delete) - 1
