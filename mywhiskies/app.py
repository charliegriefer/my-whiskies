import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask

from mywhiskies.blueprints.auth.views import auth
from mywhiskies.blueprints.bottle.views import bottle
from mywhiskies.blueprints.bottler.views import bottler
from mywhiskies.blueprints.core.views import core
from mywhiskies.blueprints.distillery.views import distillery
from mywhiskies.blueprints.errors.views import errors
from mywhiskies.blueprints.user.views import user
from mywhiskies.extensions import register_extensions

dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
load_dotenv(dotenv_path=dotenv_path, verbose=True)


def create_app(settings_override=None):
    """
    Create a Flask app using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(os.environ["CONFIG_TYPE"])

    if settings_override:
        app.config.update(settings_override)

    @app.context_processor
    def inject_today_date():
        return {"current_date": datetime.today()}

    app.register_blueprint(auth)
    app.register_blueprint(core)
    app.register_blueprint(bottle)
    app.register_blueprint(bottler)
    app.register_blueprint(distillery)
    app.register_blueprint(errors)
    app.register_blueprint(user)
    register_extensions(app)

    return app
