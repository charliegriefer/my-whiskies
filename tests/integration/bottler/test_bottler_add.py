from flask import Flask, url_for
from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.bottler.forms import BottlerAddForm
from mywhiskies.blueprints.user.models import User
from tests.conftest import TEST_USER_PASSWORD


def test_add_bottler_requires_login(app: Flask):
    with app.test_client() as client:
        response = client.get(url_for("bottler.bottler_add"), follow_redirects=False)
        assert response.status_code == 302
        assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_form(app: Flask, test_user: User):
    with app.app_context():
        user_bottlers_count = len(test_user.bottlers)

        formdata = MultiDict(
            {
                "name": "Fierce & Kind",
                "region_1": "Oceanside",
                "region_2": "CA",
                "url": "https://fiercenkind.com/",
            }
        )

        form = BottlerAddForm()
        form.process(formdata)

        assert form.validate(), f"Form validation failed: {form.errors}"

        # Submit the form and follow the redirect
        with app.test_client() as client:
            # log in the test user
            client.post(
                url_for("auth.login"),
                data={
                    "username": test_user.username,
                    "password": TEST_USER_PASSWORD,
                },
            )
            response = client.post(
                url_for("bottler.bottler_add"), data=formdata, follow_redirects=True
            )

            # Check that the user is redirected to the home page
            assert response.status_code == 200
            assert (
                url_for("core.home", username=test_user.username)
                in response.request.url
            )

            # Check that the flash message is in the response data
            bottler_name = formdata["name"]
            assert (
                f'"{bottler_name}" has been successfully added.'
                in response.get_data(as_text=True)
            )

        assert len(test_user.bottlers) == user_bottlers_count + 1
