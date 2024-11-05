from flask import Flask, url_for

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_PASSWORD, html_encode


def test_bottle_list(app: Flask, test_user: User):
    with app.test_client() as client:
        response = client.get(
            url_for("bottle.list_bottles", username=test_user.username)
        )
        assert response.status_code == 200
        suffix = "'s" if not test_user.username.endswith("s") else "'"
        expected_title = html_encode(f"{test_user.username}{suffix} Whiskies")
        assert expected_title.encode("utf-8") in response.data
        for bottle in test_user.bottles:
            assert bottle.name.encode("utf-8") in response.data
            assert bottle.type.name.encode("utf-8") in response.data
            if bottle.abv:
                assert bottle.abv.encode("utf-8") in response.data
            assert bottle.description.encode("utf-8") in response.data


def test_bottle_list_logged_in_elements(
    app: Flask, test_user: User, npc_user: User, test_user_bottle: Bottle
):
    with app.test_client() as client:
        # log in the test user
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )

        # get the bottle list page for another user.
        # even though we're logged in, we shouldn't see edit or delete icons in another user's list.
        response = client.get(
            url_for("bottle.list_bottles", username=npc_user.username)
        )
        assert response.status_code == 200
        assert b"Random Bottle" not in response.data
        assert b"bi-pencil" not in response.data
        assert b"bi-trash" not in response.data

        # get the bottle list page the current user.
        # now we should see the edit and delete iconss, as well as the "random" button.
        response = client.get(
            url_for("bottle.list_bottles", username=test_user.username)
        )
        assert response.status_code == 200
        assert b"Random Bottle" in response.data
        assert b"bi-pencil" in response.data
        assert b"bi-trash" in response.data


def test_bottle_list_logged_out_elements(app: Flask):
    with app.test_client() as client:
        # not logged in, so we shouldn't see the random bottle button, or any edit or delete icons in any lists.
        response = client.get(url_for("bottle.list_bottles", username="testuser"))
        assert b"Random Bottle" not in response.data
        assert b"bi-pencil" not in response.data
        assert b"bi-trash" not in response.data

        response = client.get(url_for("bottle.list_bottles", username="testuser"))
        assert b"Random Bottle" not in response.data
        assert b"bi-pencil" not in response.data
        assert b"bi-trash" not in response.data
