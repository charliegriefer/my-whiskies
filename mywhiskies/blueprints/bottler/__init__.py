from flask import Blueprint

bottler_bp = Blueprint("bottler", __name__, template_folder="templates")

from .views import bottler  # noqa: E402, F401
