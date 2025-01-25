from flask import current_app, request

from mywhiskies.blueprints.user.models import UserLogin
from mywhiskies.extensions import db


def log_user_login(sender, user):
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    login_entry = UserLogin(
        user_id=user.id, login_date=db.func.now(), ip_address=ip_address
    )
    db.session.add(login_entry)
    db.session.commit()

    current_app.logger.info(f"User {user.username} logged in from {ip_address}")
