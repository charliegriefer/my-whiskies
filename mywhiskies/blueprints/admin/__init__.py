from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")

from .views import admin  # noqa: E402, F401
