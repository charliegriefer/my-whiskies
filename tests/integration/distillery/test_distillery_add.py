from flask import url_for
from flask.testing import FlaskClient
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.distillery.forms import DistilleryForm
from mywhiskies.blueprints.user.models import User

new_distillery_formdata = MultiDict(
    {
        "name": "Ironroot Republic",
        "region_1": "Denison",
        "region_2": "TX",
        "url": "https://www.ironrootrepublic.com/",
    }
)


def test_add_distillery_requires_login(client: FlaskClient, test_user_01: User) -> None:
    response = client.get(
        url_for("distillery.distillery_add", username=test_user_01.username),
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_distillery_form(client: FlaskClient) -> None:
    """Test that a valid distillery form passes validation."""
    form = DistilleryForm()
    form.process(new_distillery_formdata)

    assert form.validate(), f"Form validation failed: {form.errors}"


def test_add_distillery(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    """Test that a logged-in user can add a distillery."""
    client = logged_in_user_01
    user_distilleries_count = len(test_user_01.distilleries)

    response = client.post(
        url_for("distillery.distillery_add", username=test_user_01.username),
        data=new_distillery_formdata,
        follow_redirects=True,
    )

    # Check that the user is redirected to the home page
    assert response.status_code == 200
    assert url_for("core.main") in response.request.url

    # Check that the flash message is in the response data
    distillery_name = new_distillery_formdata["name"]
    assert f'"{distillery_name}" has been successfully added.' in response.get_data(
        as_text=True
    )

    assert len(test_user_01.distilleries) == user_distilleries_count + 1
