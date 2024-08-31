import os

import pytest

from app import create_app
from my_whiskies.extensions import db


@pytest.fixture
def test_app():
    os.environ["CONFIG_TYPE"] = "config.TestConfig"

    test_app = create_app()

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()
