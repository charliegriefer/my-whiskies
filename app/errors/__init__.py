from flask import Blueprint

errors_blueprint = Blueprint("errors", __name__)

from app.errors import handlers
