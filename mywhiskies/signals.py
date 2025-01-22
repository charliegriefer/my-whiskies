from flask_login import user_logged_in

from mywhiskies.common.signals import log_user_login


def register_signals(app):
    """Registers signals with the Flask app."""
    with app.app_context():
        user_logged_in.connect(log_user_login, app)
