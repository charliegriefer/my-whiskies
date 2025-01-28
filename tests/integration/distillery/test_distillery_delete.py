from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User


def test_delete_distillery_not_logged_in(
    client: FlaskClient, test_user_01: User
) -> None:
    """Test that a user must be logged in to delete a distillery."""
    response = client.get(
        url_for(
            "distillery.delete",
            username=test_user_01.username,
            distillery_id=test_user_01.distilleries[0].id,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Please log in to access this page." in response.get_data(as_text=True)


def test_delete_not_my_distillery(
    logged_in_user_01: FlaskClient, test_user_01: User, test_user_02: User
) -> None:
    """Test that even if logged in, a user cannot delete another user's distillery."""
    client = logged_in_user_01
    response = client.get(
        url_for(
            "distillery.delete",
            username=test_user_01.username,
            distillery_id=test_user_02.distilleries[0].id,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "There was an issue deleting this distillery" in response.get_data(
        as_text=True
    )


def test_delete_my_distillery_has_bottles(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    client = logged_in_user_01
    # the test user should have two distilleries. One with a bottle associated, and one without.
    for distillery in test_user_01.distilleries:
        response = client.get(
            url_for(
                "distillery.delete",
                username=test_user_01.username,
                distillery_id=distillery.id,
            ),
            follow_redirects=True,
        )
        if distillery.bottles:
            assert response.status_code == 200
            assert "Cannot delete" in response.get_data(as_text=True)
        else:
            assert response.status_code == 200
            assert "has been successfully deleted" in response.get_data(as_text=True)
            assert "Cannot delete" not in response.get_data(as_text=True)
