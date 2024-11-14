import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask

from config import DevConfig, ProdConfig
from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.blueprints.core import core_bp
from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.blueprints.errors.views import errors
from mywhiskies.extensions import register_extensions

load_dotenv()


def create_app(settings_override: dict = None) -> Flask:
    config_type = os.getenv("CONFIG_TYPE", "config.DevConfig")
    config_class = DevConfig if config_type == "config.DevConfig" else ProdConfig

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config_class)

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


app = create_app()
