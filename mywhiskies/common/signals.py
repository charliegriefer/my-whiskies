from datetime import datetime, timezone

from flask import current_app, request

from mywhiskies.extensions import db
from mywhiskies.models import UserLogin
from mywhiskies.services.auth.email import send_new_login_alert
from mywhiskies.services.auth.login import is_new_ip


def log_user_login(sender, user):
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    alert = is_new_ip(user.id, ip_address)

    login_entry = UserLogin(user_id=user.id, login_date=db.func.now(), ip_address=ip_address)
    db.session.add(login_entry)

    user.last_login_at = datetime.now(timezone.utc)
    if user.warned_at is not None:
        user.warned_at = None

    db.session.commit()

    if alert:
        send_new_login_alert(user, ip_address)

    current_app.logger.info(f"User {user.username} logged in from {ip_address}")
