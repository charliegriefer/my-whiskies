from flask import Flask, url_for

from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_PASSWORD


def test_delete_bottler_not_logged_in(
    app: Flask,
    test_user_bottler: Bottler,
) -> None:
    """Test that a user must be logged in to delete a bottler."""
    with app.test_client() as client:
        response = client.get(
            url_for("bottler.bottler_delete", bottler_id=test_user_bottler.id),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Please log in to access this page." in response.data


def test_delete_not_my_bottler(app: Flask, test_user: User, npc_user: User) -> None:
    """Test that even if logged in, a user cannot delete another user's bottler."""
    with app.test_client() as client:
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )
        response = client.get(
            url_for("bottler.bottler_delete", bottler_id=npc_user.bottlers[0].id),
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"There was an issue deleting this bottler" in response.data
