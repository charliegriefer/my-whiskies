import os
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, g, request
from flask_login import current_user
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
from mywhiskies.logging import register_logging
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

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

    # add datetime to template context
    app.jinja_env.globals["datetime"] = datetime

    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())

    @app.after_request
    def after_request(response):
        if not app.testing:
            # Skip logging for static files
            if not request.path.startswith("/static/"):
                duration_ms = int((time.time() - g.start_time) * 1000)
                extra = {
                    "duration_ms": duration_ms,
                    "request_id": g.request_id,
                    "ip": request.remote_addr,
                    "status_code": response.status_code,
                }
                if current_user.is_authenticated:
                    extra["user"] = current_user.email

                app.logger.info(
                    f"{request.method} {request.path} [{response.status_code}]",
                    extra=extra,
                )
        return response

    app.register_blueprint(auth)
    app.register_blueprint(core_bp)
    app.register_blueprint(bottle_bp)
    app.register_blueprint(bottler_bp)
    app.register_blueprint(distillery_bp)
    app.register_blueprint(errors)
    app.register_blueprint(user_bp)

    register_logging(app)
    register_extensions(app)
    register_signals(app)

    return app


app = create_app()
