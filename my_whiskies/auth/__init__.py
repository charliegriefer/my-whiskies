from flask import Blueprint

auth_blueprint = Blueprint("auth", __name__)

from my_whiskies.auth import routes  # noqa: E402

__all__ = ["routes"]
