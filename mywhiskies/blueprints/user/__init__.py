from flask import Blueprint

user_bp = Blueprint("user", __name__, template_folder="templates")

from .views import user  # noqa: E402, F401
