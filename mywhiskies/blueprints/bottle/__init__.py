from flask import Blueprint

bottle_bp = Blueprint("bottle", __name__, template_folder="templates")

from .views import bottle  # noqa: E402, F401
