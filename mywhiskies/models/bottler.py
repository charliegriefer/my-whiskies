import uuid
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa

from mywhiskies.extensions import db
from sqlalchemy import String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, Session as OrmSession, mapped_column, relationship

if TYPE_CHECKING:
    from mywhiskies.models import Bottle, User


class Bottler(db.Model):
    __tablename__ = "bottler"
    __table_args__ = (UniqueConstraint("user_id", "user_num", name="uq_bottler_user_num"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(65))
    user_num: Mapped[int]
    description: Mapped[Optional[str]] = mapped_column(Text)
    region_1: Mapped[str] = mapped_column(String(36))
    region_2: Mapped[str] = mapped_column(String(36))
    url: Mapped[Optional[str]] = mapped_column(String(64))

    # foreign_keys
    user_id: Mapped[str] = mapped_column(db.ForeignKey("user.id"))

    # relationships
    user: Mapped["User"] = relationship(back_populates="bottlers")
    bottles: Mapped[List["Bottle"]] = relationship(back_populates="bottler")


@event.listens_for(Bottler, "before_insert")
def bottle_before_insert(mapper, connect, target) -> None:
    clean_bottler_data(target)
    result = connect.execute(
        sa.text("SELECT COALESCE(MAX(user_num), 0) FROM bottler WHERE user_id = :uid"),
        {"uid": target.user_id},
    )
    db_max = result.scalar()
    session = OrmSession.object_session(target)
    pending_max = (
        max(
            (obj.user_num for obj in session.new
             if isinstance(obj, Bottler)
             and obj.user_id == target.user_id
             and obj is not target
             and obj.user_num is not None),
            default=0,
        )
        if session is not None else 0
    )
    target.user_num = max(db_max, pending_max) + 1


@event.listens_for(Bottler, "before_update")
def bottle_before_update(mapper, connect, target) -> None:
    clean_bottler_data(target)


def clean_bottler_data(target) -> None:
    target.name = target.name.strip()
    target.description = target.description.strip() if target.description else None
    target.url = target.url.strip() if target.url else None
