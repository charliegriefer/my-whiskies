from flask import Blueprint

auth_blueprint = Blueprint("auth", __name__)

from app.auth import routes  # noqa: E402

__all__ = ["routes"]
