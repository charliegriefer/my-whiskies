from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.user.models import User


def test_delete_bottle_not_logged_in(client: FlaskClient, test_user_01: User) -> None:
    """Test that a user must be logged in to delete a bottle."""
    bottle_to_delete: Bottle = test_user_01.bottles[0]
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=bottle_to_delete.id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_bottle(
    logged_in_user: FlaskClient, test_user_01: User, test_user_02: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's bottle."""
    client = logged_in_user
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=test_user_02.bottles[0].id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "There was an issue deleting this bottle" in response.get_data(as_text=True)


def test_delete_my_bottle(logged_in_user: FlaskClient, test_user_01: User) -> None:
    client = logged_in_user
    bottles_before_delete = [bottle.name for bottle in test_user_01.bottles]

    bottle_to_delete: Bottle = test_user_01.bottles[0]

    # Perform the delete operation
    response = client.get(
        url_for("bottle.bottle_delete", bottle_id=bottle_to_delete.id),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Bottle deleted successfully" in response.get_data(as_text=True)

    bottles_after_delete = [bottle.name for bottle in test_user_01.bottles]

    assert len(bottles_after_delete) == len(bottles_before_delete) - 1
