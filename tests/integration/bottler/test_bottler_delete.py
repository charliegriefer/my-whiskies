from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import User


def test_delete_bottler_not_logged_in(client: FlaskClient, test_user_01: User) -> None:
    """Test that a user must be logged in to delete a bottler."""
    bottler = test_user_01.bottlers[0]
    response = client.get(
        url_for(
            "bottler.delete",
            username=test_user_01.username,
            user_num=bottler.user_num,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_bottler(
    logged_in_user_01: FlaskClient, test_user_01: User, test_user_02: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's bottler."""
    client = logged_in_user_01
    bottler = test_user_02.bottlers[0]
    response = client.get(
        url_for(
            "bottler.delete",
            username=test_user_02.username,
            user_num=bottler.user_num,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_delete_my_bottler_has_bottles(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    client = logged_in_user_01
    # the test user should have two bottlers. One with a bottle associated, and one without.
    for bottler in test_user_01.bottlers:
        response = client.get(
            url_for(
                "bottler.delete",
                username=test_user_01.username,
                user_num=bottler.user_num,
            ),
            follow_redirects=True,
        )
        if bottler.bottles:
            assert response.status_code == 200
            assert "Cannot delete" in response.get_data(as_text=True)
        else:
            assert response.status_code == 200
            assert "has been successfully deleted" in response.get_data(as_text=True)
            assert "Cannot delete" not in response.get_data(as_text=True)
