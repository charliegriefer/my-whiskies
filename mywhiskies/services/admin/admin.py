from datetime import datetime, timezone

from mywhiskies.extensions import db
from mywhiskies.models import User


def get_user_stats() -> dict:
    base = db.select(User).filter_by(is_deleted=False)
    total = db.session.execute(base).scalars().all()
    return {
        "total": len(total),
        "active": sum(1 for u in total if u.is_active and u.email_confirmed),
        "disabled": sum(1 for u in total if not u.is_active),
        "unverified": sum(1 for u in total if not u.email_confirmed),
    }


def get_all_users() -> list[User]:
    return db.session.execute(db.select(User).filter_by(is_deleted=False).order_by(User.username)).scalars().all()


def create_user(username: str, email: str, password: str, pre_verified: bool) -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    if pre_verified:
        user.email_confirmed = True
        user.email_confirm_date = datetime.now(timezone.utc)
    db.session.add(user)
    db.session.commit()
    return user


def toggle_user_active(user: User) -> bool:
    user.is_active = not user.is_active
    db.session.commit()
    return user.is_active
