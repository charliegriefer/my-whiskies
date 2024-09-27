import os
from datetime import datetime
from logging.config import dictConfig

import flask
from dotenv import load_dotenv
from flask import Flask

from app.extensions import db, login_manager, mail, migrate

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ["CONFIG_TYPE"])

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "formatter": "default",
                    "filename": "logs/my-whiskies.log",
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 5
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": app.config["LOG_LEVEL"],
                }
            }
        }
    )

    @app.context_processor
    def inject_today_date():
        return {"current_date": datetime.today()}

    @app.before_request
    def before_request():
        flask.session.permanent = True
        app.permanent_session_lifetime = app.permanent_session_lifetime
        flask.session.modified = True

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

    return app
