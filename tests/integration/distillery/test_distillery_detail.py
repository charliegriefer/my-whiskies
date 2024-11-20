from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User


def test_distillery_detail_no_bottles(client: FlaskClient, test_user_02: User) -> None:
    """
    A non-logged in user viewing a user's distilleries

    Parameters:
        client (FlaskClient)
        test_user_02 (User): A user that has a distillery with no bottles.

    Returns:
        None
    """
    distillery_id = _get_ironroot(test_user_02)

    response = client.get(
        url_for("distillery.distillery_detail", distillery_id=distillery_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Ironroot Republic" in response_data
    assert "has no bottles from Ironroot Republic" in response_data
    assert "Random Bottle" not in response_data


def test_distillery_detail_has_bottle(client: FlaskClient, test_user_01: User) -> None:
    """
    A non-logged in user viewing a user's distilleries

    Parameters:
        client (FlaskClient)
        test_user_01 (User): A user that has a distillery with a bottle.

    Returns:
        None
    """
    distillery_id = _get_frey_ranch(test_user_01)

    response = client.get(
        url_for("distillery.distillery_detail", distillery_id=distillery_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Frey Ranch" in response_data
    assert "Frey Ranch Straight Rye Whiskey" in response_data
    assert "Random Bottle" not in response_data


def test_distillery_detail_no_bottles_my_distillery(
    logged_in_user_02: FlaskClient, test_user_02: User
) -> None:
    """
    A logged-in user viewing one of their own distilleries with no bottles.

    Parameters:
        logged_in_user_02 (FlaskClient)
        test_user_02 (User): A user that has a bottler with no bottles.

    Returns:
        None
    """
    distillery_id = _get_ironroot(test_user_02)

    response = logged_in_user_02.get(
        url_for("distillery.distillery_detail", distillery_id=distillery_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Ironroot Republic" in response_data
    assert (
        f"{test_user_02.username} has no bottles from Ironroot Republic"
        in response_data
    )
    assert (
        "Random Bottle" not in response_data
    )  # not in response data since there are no bottles.


def test_distillery_detail_bottles_my_distillery(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    """
    A logged-in user viewing one of their own distilleries with a bottle.

    Parameters:
        logged_in_user_01 (FlaskClient)
        test_user_01 (User): A user that has a distillery with bottles.

    Returns:
        None
    """
    distillery_id = _get_frey_ranch(test_user_01)

    response = logged_in_user_01.get(
        url_for("distillery.distillery_detail", distillery_id=distillery_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Frey Ranch" in response_data
    assert "Frey Ranch Straight Rye Whiskey" in response_data
    # assert "Random Bottle" in response_data


def _get_ironroot(test_user_02: User) -> str:
    """Convenience method to return a user's distillery"""
    for distillery in test_user_02.distilleries:
        if distillery.name == "Ironroot Republic":
            return distillery.id


def _get_frey_ranch(test_user_01: User) -> str:
    """Convenience method to return a user's distillery"""
    for distillery in test_user_01.distilleries:
        if distillery.name == "Frey Ranch":
            return distillery.id
