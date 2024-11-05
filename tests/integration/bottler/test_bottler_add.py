from flask import Flask, url_for

from mywhiskies.blueprints.bottler.forms import BottlerAddForm
from mywhiskies.blueprints.user.models import User
from mywhiskies.services.bottler.bottler import add_bottler


def test_add_bottler_requires_login(app: Flask):
    with app.test_client() as client:
        response = client.get(url_for("bottler.bottler_add"), follow_redirects=False)
        assert response.status_code == 302
        assert url_for("auth.login", _external=False) in response.headers["Location"]


def test_valid_bottler_form(app: Flask, test_user: User):
    with app.app_context():
        user_bottlers_count = len(test_user.bottlers)

        formdata = {
            "name": "Fierce & Kind",
            "location_1": "Oceanside",
            "location_2": "CA",
            "url": "https://fiercenkind.com/",
        }

        form = BottlerAddForm()
        form.process(formdata)

        assert form.validate(), f"Form validation failed: {form.errors}"

        add_bottler(form, test_user)
        assert len(test_user.bottlers) == user_bottlers_count + 1
