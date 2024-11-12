from flask import Blueprint

distillery_bp = Blueprint("distillery", __name__, template_folder="templates")

from .views import distillery  # noqa: E402, F401
