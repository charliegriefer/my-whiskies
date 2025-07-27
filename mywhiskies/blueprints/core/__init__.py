from flask import Blueprint

core_bp = Blueprint("core", __name__, template_folder="templates")

from .views import core  # noqa: E402, F401
