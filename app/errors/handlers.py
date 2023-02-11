from flask import current_app, render_template, request

from app import db
from app.errors import errors_blueprint


@errors_blueprint.app_errorhandler(404)
def not_found_error(error):
    msg = f"{error} | {request.path}"
    current_app.logger.debug(msg)
    return render_template("errors/404.html"), 404


@errors_blueprint.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.debug(f"The 500 handler. {error}")
    return render_template("errors/500.html"), 500
