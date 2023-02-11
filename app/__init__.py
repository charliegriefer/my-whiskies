import os

from flask import Flask

from app.extensions import db, login_manager, mail, migrate


def create_app():
    app = Flask(__name__)

    config_type = os.getenv("CONFIG_TYPE", default="config.DevConfig")
    app.config.from_object(config_type)

    app.logger.setLevel(app.config["LOG_LEVEL"])

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    mail.init_app(app)
    migrate.init_app(app, db)

    # register blueprints
    from app.auth import auth_blueprint
    from app.errors import errors_blueprint
    from app.main import main_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(errors_blueprint)
    app.register_blueprint(main_blueprint)

    from app.models import bottle, user

    return app
