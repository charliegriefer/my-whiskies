from flask import Blueprint

main_blueprint = Blueprint("main", __name__)

from app.main import routes  # noqa: E402

__all__ = ["routes"]
