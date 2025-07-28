import os

from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()


def register_extensions(app):
    # Import all models to ensure they're registered with SQLAlchemy before db.init_app()
    from mywhiskies.models import (  # noqa: F401
        Bottle,
        BottleImage,
        Bottler,
        Distillery,
        User,
        UserLogin,
        bottle_distillery,
    )

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    migrations_dir = os.path.join(os.path.dirname(app.root_path), "migrations")
    migrate.init_app(app, db, directory=migrations_dir)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
