from flask import Blueprint

payments_bp = Blueprint("payments", __name__, template_folder="templates")

from .views import payments  # noqa: E402, F401
