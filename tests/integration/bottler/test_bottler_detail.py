from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import User


def test_distillery_detail_no_bottles(client: FlaskClient, test_user_02: User) -> None:
    """
    A non-logged in user viewing a user's bottler

    Parameters:
        client (FlaskClient)
        test_user_02 (User): A user that has a bottler with no bottles.

    Returns:
        None
    """
    bottler = _get_crowded_barrel(test_user_02)

    response = client.get(
        url_for("bottler.detail", username=test_user_02.username, user_num=bottler.user_num)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Crowded Barrel Whiskey Co." in response_data
    assert "has no bottles from Crowded Barrel Whiskey Co.. Yet." in response_data
    assert "Random Bottle" not in response_data


def test_bottler_detail_has_bottle(client: FlaskClient, test_user_01: User) -> None:
    """
    A non-logged in user viewing a user's bottler

    Parameters:
        client (FlaskClient)
        test_user_01 (User): A user that has a bottler with a bottle.

    Returns:
        None
    """
    bottler = _get_lost_lantern(test_user_01)

    response = client.get(
        url_for("bottler.detail", username=test_user_01.username, user_num=bottler.user_num)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Lost Lantern" in response_data
    assert "Far-Flung Bourbon I" in response_data
    assert "Random Bottle" not in response_data


def test_bottler_detail_no_bottles_my_bottler(
    logged_in_user_02: FlaskClient, test_user_02: User
) -> None:
    """
    A logged-in user viewing one of their own bottlers with no bottles.

    Parameters:
        logged_in_user_02 (FlaskClient)
        test_user_02 (User): A user that has a bottler with no bottles.

    Returns:
        None
    """
    bottler = _get_crowded_barrel(test_user_02)

    response = logged_in_user_02.get(
        url_for("bottler.detail", username=test_user_02.username, user_num=bottler.user_num)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Crowded Barrel Whiskey Co." in response_data
    assert "has no bottles from Crowded Barrel Whiskey Co.. Yet." in response_data
    assert "Random Bottle" not in response_data


def test_bottler_detail_bottles_my_bottler(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    """
    A logged-in user viewing one of their own bottlers with a bottle.

    Parameters:
        logged_in_user_01 (FlaskClient)
        test_user_01 (User): A user that has a bottler with one bottle.

    Returns:
        None
    """
    bottler = _get_lost_lantern(test_user_01)

    response = logged_in_user_01.get(
        url_for("bottler.detail", username=test_user_01.username, user_num=bottler.user_num)
    )
    response_data = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Lost Lantern" in response_data
    assert "Far-Flung Bourbon I" in response_data
    assert "Random Bottle" not in response_data


def _get_crowded_barrel(user: User):
    """Convenience method to return a user's bottler"""
    for bottler in user.bottlers:
        if bottler.name == "Crowded Barrel Whiskey Co.":
            return bottler


def _get_lost_lantern(user: User):
    """Convenience method to return a user's bottler"""
    for bottler in user.bottlers:
        if bottler.name == "Lost Lantern":
            return bottler
