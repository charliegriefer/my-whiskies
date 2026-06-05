from flask import Blueprint

auth = Blueprint("auth", __name__, template_folder="templates")

from .views import login, passkey, password, registration  # noqa: E402, F401
