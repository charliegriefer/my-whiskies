from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import Bottle, User


def test_delete_bottle_not_logged_in(client: FlaskClient, test_user_01: User) -> None:
    """Test that a user must be logged in to delete a bottle."""
    bottle_to_delete: Bottle = test_user_01.bottles[0]
    response = client.get(
        url_for(
            "bottle.delete",
            username=test_user_01.username,
            user_num=bottle_to_delete.user_num,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_bottle(
    logged_in_user_01: FlaskClient, test_user_01: User, test_user_02: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's bottle."""
    client = logged_in_user_01
    bottle = test_user_02.bottles[0]
    response = client.get(
        url_for(
            "bottle.delete",
            username=test_user_02.username,
            user_num=bottle.user_num,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "There was an issue deleting this bottle" in response.get_data(as_text=True)


def test_delete_my_bottle(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    client = logged_in_user_01
    bottles_before_delete = [bottle.name for bottle in test_user_01.bottles]

    bottle_to_delete: Bottle = test_user_01.bottles[0]

    response = client.get(
        url_for(
            "bottle.delete",
            username=test_user_01.username,
            user_num=bottle_to_delete.user_num,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bottle deleted successfully" in response.get_data(as_text=True)

    bottles_after_delete = [bottle.name for bottle in test_user_01.bottles]

    assert len(bottles_after_delete) == len(bottles_before_delete) - 1
