from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.blueprints.user.models import User


def test_private_bottle_logged_out(client: FlaskClient, test_user_01: User) -> None:
    """
    Ensure that a logged out user cannot view a private bottle.

    Parameters:
        client (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_ironroot_bottle(test_user_01)

    response = client.get(url_for("bottle.bottle_detail", bottle_id=bottle_id))
    assert response.status_code == 404


def test_private_bottle_logged_in(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    """
    Ensure that a logged in user can view their own private bottle.

    Parameters:
        logged_in_user_01 (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_ironroot_bottle(test_user_01)
    response = logged_in_user_01.get(
        url_for(
            "bottle.bottle_detail", username=test_user_01.username, bottle_id=bottle_id
        )
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Is Private" in response_data


def test_private_bottle_logged_in_not_my_bottle(
    logged_in_user_02: FlaskClient, test_user_01: User
) -> None:
    """
    Ensure that a logged in user cannot view another user's private bottle.

    Parameters:
        logged_in_user_02 (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_ironroot_bottle(test_user_01)
    response = logged_in_user_02.get(
        url_for("bottle.bottle_detail", bottle_id=bottle_id)
    )
    assert response.status_code == 404


def test_personal_note_logged_out(client: FlaskClient, test_user_01: User) -> None:
    """
    Ensure that a logged out user cannot see a bottle's "personal note".

    Parameters:
        client (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_frey_ranch_bottle(test_user_01)

    response = client.get(url_for("bottle.bottle_detail", bottle_id=bottle_id))
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Personal Note" not in response_data


def test_personal_note_logged_in(
    logged_in_user_01: FlaskClient, test_user_01: User
) -> None:
    """
    Ensure that a logged in user can see their own bottle's "personal note".

    Parameters:
        logged_in_user_01 (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_frey_ranch_bottle(test_user_01)

    response = logged_in_user_01.get(
        url_for("bottle.bottle_detail", bottle_id=bottle_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Personal Note" in response_data


def test_personal_note_logged_in_not_my_bottle(
    logged_in_user_02: FlaskClient, test_user_01: User
) -> None:
    """
    Ensure that a logged in user cannot see another user's bottle's "personal note".

    Parameters:
        logged_in_user_02 (FlaskClient)
        test_user_01 (User): A user that has a bottle with a personal note.

    Returns:
        None
    """
    bottle_id = _get_frey_ranch_bottle(test_user_01)

    response = logged_in_user_02.get(
        url_for("bottle.bottle_detail", bottle_id=bottle_id)
    )
    response_data = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Personal Note" not in response_data


def _get_frey_ranch_bottle(test_user_01: User) -> str:
    """Convenience method to return a bottle with a personal note value"""
    for bottle in test_user_01.bottles:
        if bottle.name == "Frey Ranch Straight Rye Whiskey":
            return bottle.id


def _get_ironroot_bottle(test_user_01: User) -> str:
    """Convenience method to return a private bottle"""
    for bottle in test_user_01.bottles:
        if bottle.name == "Ironroot Republic Hubris Hazmat":
            return bottle.id
