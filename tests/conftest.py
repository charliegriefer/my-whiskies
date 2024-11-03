import os
import sys

import pytest

# Ensure the parent directory is added to the system path before imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from mywhiskies.app import create_app  # noqa: E402

# from mywhiskies.blueprints.user.models import User  # noqa: E402
from mywhiskies.extensions import db  # noqa: E402


@pytest.fixture(scope="session")
def app():
    app = create_app(config_class=TestConfig)
    app.teardown_bkp = app.teardown_appcontext_funcs
    app.teardown_appcontext_funcs = []
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# @pytest.fixture
# def test_user(app):
#     """Create a test user."""
#     with app.app_context():
#         user = User(username="testuser", email="test@example.com")
#         user.set_password("testpass")
#         db.session.add(user)
#         db.session.commit()  # This will go to the test database
#     return user
