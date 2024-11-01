import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask

from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.blueprints.core import core_bp
from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.blueprints.errors.views import errors
from mywhiskies.extensions import register_extensions

dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)
load_dotenv(dotenv_path=dotenv_path, verbose=True)


def create_app(settings_override: dict = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(os.environ["CONFIG_TYPE"])

    if settings_override:
        app.config.update(settings_override)

    @app.context_processor
    def inject_today_date():
        return {"current_date": datetime.today()}

    app.register_blueprint(auth)
    app.register_blueprint(core_bp)
    app.register_blueprint(bottle_bp)
    app.register_blueprint(bottler_bp)
    app.register_blueprint(distillery_bp)
    app.register_blueprint(errors)
    register_extensions(app)

    return app
