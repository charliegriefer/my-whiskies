from flask import Flask, url_for

from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_PASSWORD


def html_encode(text: str) -> str:
    """HTML encodes characters in a string in order to be able to search for that string in response.data"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


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


def test_random_bottle_button_logged_in(app: Flask, test_user: User):
    with app.test_client() as client:
        # log in the test user
        client.post(
            url_for("auth.login"),
            data={
                "username": test_user.username,
                "password": TEST_PASSWORD,
            },
        )

        # Access the user's bottle list page
        response = client.get(
            url_for("bottle.list_bottles", username=test_user.username)
        )
        assert response.status_code == 200

        # Check that the random bottle button is present in the response
        assert b"Random Bottle" in response.data  # Adjust the button text accordingly


def test_random_bottle_button_not_logged_in(app: Flask):
    with app.test_client() as client:
        # Get the bottle list without logging in
        response = client.get(url_for("bottle.list_bottles", username="testuser"))

        # Check if the random bottle button is not displayed
        assert b"Random Bottle" not in response.data
