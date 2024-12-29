from flask import url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.bottler.forms import BottlerAddForm
from mywhiskies.blueprints.user.models import User

new_bottler_formdata = MultiDict(
    {
        "name": "Fierce & Kind",
        "region_1": "Oceanside",
        "region_2": "CA",
        "url": "https://fiercenkind.com/",
    }
)


def test_add_bottler_requires_login(client: FlaskClient) -> None:
    response = client.get(
        url_for("bottler.bottler_add", username="skibidi"), follow_redirects=False
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_form() -> None:
    """Test that a valid bottler form passes validation."""
    form = BottlerAddForm()
    form.process(new_bottler_formdata)

    assert form.validate(), f"Form validation failed: {form.errors}"


def test_add_bottler(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    """Test that a logged-in user can add a bottler."""
    client = logged_in_user_01
    user_bottlers_count = len(test_user_01.bottlers)

    response = client.post(
        url_for("bottler.bottler_add", username=test_user_01.username),
        data=new_bottler_formdata,
        follow_redirects=True,
    )

    # Check that the user is redirected to the home page
    assert response.status_code == 200
    assert url_for("core.main") in response.request.url

    # Check that the flash message is in the response data
    bottler_name = new_bottler_formdata["name"]
    assert f'"{bottler_name}" has been successfully added.' in response.get_data(
        as_text=True
    )

    assert len(test_user_01.bottlers) == user_bottlers_count + 1
