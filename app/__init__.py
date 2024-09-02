import os
from datetime import datetime

import flask
from dotenv import load_dotenv
from flask import Flask

from app.extensions import db, login, mail, migrate
from app.models import User

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=True)


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ["CONFIG_TYPE"])

    initialize_extensions(app)
    register_blueprints(app)
    set_contexts(app)

    @app.before_request
    def before_request():
        flask.session.permanent = True
        app.permanent_session_lifetime = app.permanent_session_lifetime
        flask.session.modified = True

    return app


def initialize_extensions(app) -> None:
    db.init_app(app)
    login.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    from app.models import User

    @login.user_loader
    def load_user(user_id: str) -> User:
        user = db.get_or_404(User, user_id)
        return user


def register_blueprints(app) -> None:
    from app.auth import auth_blueprint
    from app.errors import errors_blueprint
    from app.main import main_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(errors_blueprint)
    app.register_blueprint(main_blueprint)


def set_contexts(app):
    @app.shell_context_processor
    def make_shell_context():
        return {"db": db, "User": User}

    @app.context_processor
    def inject_today_date():
        return {"current_date": datetime.today()}
