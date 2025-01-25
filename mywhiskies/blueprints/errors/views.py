from flask import Blueprint, current_app, render_template, request

from mywhiskies.extensions import db

errors = Blueprint("errors", __name__, template_folder="templates")


@errors.app_errorhandler(403)
def forbidden_error(error):
    msg = f"{error} | {request.path}"
    current_app.logger.debug(msg)
    return render_template("errors/403.html"), 403


@errors.app_errorhandler(404)
def not_found_error(error):
    msg = f"{error} | {request.path}"
    current_app.logger.debug(msg)
    return render_template("errors/404.html"), 404


@errors.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(
        f"500 Internal Server Error at {request.path}: {error}", exc_info=True
    )
    return render_template("errors/500.html"), 500
