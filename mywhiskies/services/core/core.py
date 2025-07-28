from typing import Any, Dict, List, Tuple

from flask_login import current_user
from mywhiskies.extensions import db
from mywhiskies.models import Bottle, Distillery, User
from sqlalchemy import func, select


def get_index_counts() -> Dict[str, Any]:
    return {
        "user_count": _get_user_count(),
        "distillery_count": _get_distillery_count(),
        "bottle_count": _get_bottle_count(),
        "pic_count": _get_image_count(),
        "bottle_type_counts": _get_bottle_type_counts(),
    }


def _get_user_count() -> int:
    return db.session.execute(
        select(func.count(User.id)).where(User.email_confirmed == 1)
    ).scalar()


def _get_distillery_count() -> int:
    return db.session.execute(select(func.count(Distillery.name.distinct()))).scalar()


def _get_bottle_count() -> int:
    bottle_table = _get_bottle_table()
    return db.session.execute(select(func.count(bottle_table.c.id))).scalar()


def _get_image_count() -> int:
    bottle_image_table = db.Model.metadata.tables["bottle_image"]
    return db.session.execute(select(func.count(bottle_image_table.c.id))).scalar_one()


def _get_bottle_type_counts() -> List[Tuple[str, int]]:
    bottle_table = _get_bottle_table()
    return db.session.execute(
        select(bottle_table.c.type, func.count(bottle_table.c.type))
        .group_by(bottle_table.c.type)
        .order_by(func.count(bottle_table.c.type).desc())
    ).all()


def get_user_by_username(username: str) -> User:
    if (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    ):
        return current_user
    return db.one_or_404(db.select(User).filter_by(username=username))


def get_live_bottles_for_user(user: User) -> List["Bottle"]:
    return [bottle for bottle in user.bottles if bottle.date_killed is None]


def _get_bottle_table() -> Any:
    return db.Model.metadata.tables["bottle"]
