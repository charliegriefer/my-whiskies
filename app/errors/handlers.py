from flask import current_app, render_template, request

from app import db
from app.email import send_email
from app.errors import errors_blueprint


@errors_blueprint.app_errorhandler(404)
def not_found_error(error):
    msg = f"{error} | {request.path}"
    current_app.logger.debug(msg)
    return render_template("errors/404.html"), 404


@errors_blueprint.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    send_email("My Whiskies Online ERROR",
               sender=current_app.config["MAIL_SENDER"],
               recipients=current_app.config["MAIL_ADMINS"],
               text_body=render_template("email/error.txt", error=error),
               html_body=render_template("email/error.html", error=error))
    return render_template("errors/500.html"), 500
