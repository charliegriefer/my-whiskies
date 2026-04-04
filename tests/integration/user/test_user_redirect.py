from flask import url_for
from flask.testing import FlaskClient
from mywhiskies.models import User


def test_user_redirect_to_bottle_list(
    client: FlaskClient, test_user_01: User
) -> None:
    response = client.get(f"/{test_user_01.username}")
    assert response.status_code == 302
    assert (
        url_for("bottle.list", username=test_user_01.username)
        in response.headers["Location"]
    )
