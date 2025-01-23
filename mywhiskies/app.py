import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import DevConfig, ProdConfig
from mywhiskies.blueprints.auth import auth
from mywhiskies.blueprints.bottle import bottle_bp
from mywhiskies.blueprints.bottler import bottler_bp
from mywhiskies.blueprints.core import core_bp
from mywhiskies.blueprints.distillery import distillery_bp
from mywhiskies.blueprints.errors.views import errors
from mywhiskies.blueprints.user import user_bp
from mywhiskies.extensions import register_extensions
from mywhiskies.signals import register_signals

load_dotenv()


def create_app(settings_override: dict = None, config_class: type = None) -> Flask:
    config_type = os.getenv("CONFIG_TYPE", "config.DevConfig")
    config_class = config_class or (
        DevConfig if config_type == "config.DevConfig" else ProdConfig
    )

    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)

    if settings_override:
        app.config.update(settings_override)

    log_dir = os.getenv("LOG_DIR", "../log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging configuration
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        log_file = os.path.join(log_dir, "my-whiskies.log")
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
        file_handler.setLevel(os.getenv("LOG_LEVEL", logging.INFO))
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        app.logger.addHandler(file_handler)

    app.logger.setLevel(os.getenv("LOG_LEVEL", logging.INFO))
    app.logger.info("App startup")

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

    @app.context_processor
    def inject_today_date():
        return {"current_date": datetime.today()}

    app.register_blueprint(auth)
    app.register_blueprint(core_bp)
    app.register_blueprint(bottle_bp)
    app.register_blueprint(bottler_bp)
    app.register_blueprint(distillery_bp)
    app.register_blueprint(errors)
    app.register_blueprint(user_bp)

    register_extensions(app)
    register_signals(app)

    return app


app = create_app()
