from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User


def test_delete_distillery_not_logged_in(client: FlaskClient, test_user: User) -> None:
    """Test that a user must be logged in to delete a bottler."""
    response = client.get(
        url_for(
            "distillery.distillery_delete", distillery_id=test_user.distilleries[0].id
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_distillery(
    logged_in_user: FlaskClient, test_user: User, npc_user: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's bottler."""
    client = logged_in_user
    response = client.get(
        url_for(
            "distillery.distillery_delete", distillery_id=npc_user.distilleries[0].id
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "There was an issue deleting this distillery" in response.get_data(
        as_text=True
    )


def test_delete_my_distillery_has_bottles(
    logged_in_user: FlaskClient, test_user: User
) -> None:
    client = logged_in_user
    # the test user should have two distilleries. One with a bottle associated, and one without.
    for distillery in test_user.distilleries:
        response = client.get(
            url_for("distillery.distillery_delete", distillery_id=distillery.id),
            follow_redirects=True,
        )
        if distillery.bottles:
            assert response.status_code == 200
            assert "Cannot delete" in response.get_data(as_text=True)
        else:
            assert response.status_code == 200
            assert "has been successfully deleted" in response.get_data(as_text=True)
            assert "Cannot delete" not in response.get_data(as_text=True)
