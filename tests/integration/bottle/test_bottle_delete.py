from flask import Flask, url_for

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_PASSWORD


def test_delete_bottle_not_logged_in(
    app: Flask,
    test_user: User,
    test_user_bottle: Bottle,
    test_user_bottle_to_delete: Bottle,
):
    """Test that a user must be logged in to delete a bottle."""
    with app.test_client() as client:
        response = client.get(
            url_for("bottle.bottle_delete", bottle_id=test_user_bottle_to_delete.id),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please log in to access this page." in response.data


def test_delete_not_my_bottle(app: Flask, test_user: User, npc_user: User):
    """Test that even if logged in, a user cannot delete another user's bottle."""
    with app.test_client() as client:
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )
        response = client.get(
            url_for("bottle.bottle_delete", bottle_id=npc_user.bottles[0].id),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"There was an issue deleting the bottle" in response.data


def test_delete_my_bottle(
    app: Flask,
    test_user: User,
    test_user_bottle: Bottle,
    test_user_bottle_to_delete: Bottle,
) -> None:
    with app.test_client() as client:
        # Log in the user
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )
        bottles_before_delete = [bottle.name for bottle in test_user.bottles]

        # Perform the delete operation
        response = client.get(
            url_for("bottle.bottle_delete", bottle_id=test_user_bottle_to_delete.id),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Bottle deleted successfully" in response.data

        bottles_after_delete = [bottle.name for bottle in test_user.bottles]

        assert len(bottles_after_delete) == len(bottles_before_delete) - 1
