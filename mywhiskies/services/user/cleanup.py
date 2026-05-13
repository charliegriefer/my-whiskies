from datetime import datetime, timedelta, timezone

from flask import current_app
from sqlalchemy.future import select

from mywhiskies.extensions import db
from mywhiskies.models import User
from mywhiskies.services.auth.email import send_inactive_account_warning
from mywhiskies.services.user.user import delete_user_account


def _inactivity_cutoff() -> datetime:
    days = current_app.config.get("INACTIVITY_DAYS", 180)
    return datetime.now(timezone.utc) - timedelta(days=days)


def _grace_cutoff() -> datetime:
    days = current_app.config.get("INACTIVITY_GRACE_PERIOD_DAYS", 30)
    return datetime.now(timezone.utc) - timedelta(days=days)


def get_users_to_warn() -> list[User]:
    cutoff = _inactivity_cutoff()
    stmt = select(User).where(
        User.email_confirmed == True,  # noqa: E712
        User.is_deleted == False,  # noqa: E712
        User.warned_at == None,  # noqa: E711
        User.last_login_at != None,  # noqa: E711
        User.last_login_at < cutoff,
    )
    return db.session.execute(stmt).scalars().all()


def get_users_to_delete() -> list[User]:
    cutoff = _grace_cutoff()
    stmt = select(User).where(
        User.is_deleted == False,  # noqa: E712
        User.warned_at != None,  # noqa: E711
        User.warned_at < cutoff,
    )
    return db.session.execute(stmt).scalars().all()


def warn_inactive_users() -> int:
    users = get_users_to_warn()
    grace_days = current_app.config.get("INACTIVITY_GRACE_PERIOD_DAYS", 30)
    for user in users:
        email = user.email
        try:
            send_inactive_account_warning(user, grace_days)
            user.warned_at = datetime.now(timezone.utc)
            db.session.commit()
            current_app.logger.info(f"Inactivity warning sent to {email}")
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to warn inactive user {email}")
    return len(users)


def delete_inactive_users() -> int:
    users = get_users_to_delete()
    count = 0
    for user in users:
        email = user.email
        warned_at = user.warned_at
        try:
            current_app.logger.info(f"Deleting inactive user {email} (warned_at={warned_at})")
            delete_user_account(user)
            count += 1
        except Exception:
            db.session.rollback()
            current_app.logger.exception(f"Failed to delete inactive user {email}")
    return count
