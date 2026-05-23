import uuid
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm import Session as OrmSession

from mywhiskies.extensions import db

if TYPE_CHECKING:
    from mywhiskies.models import Bottle, User


class BarrelPicker(db.Model):
    __tablename__ = "barrel_picker"
    __table_args__ = (UniqueConstraint("user_id", "user_num", name="uq_barrel_picker_user_num"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(65))
    user_num: Mapped[int]
    description: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(64))

    # foreign keys
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))

    # relationships
    user: Mapped["User"] = relationship(back_populates="barrel_pickers")
    bottles: Mapped[List["Bottle"]] = relationship(
        "Bottle", secondary="bottle_barrel_picker", back_populates="barrel_pickers"
    )


@event.listens_for(BarrelPicker, "before_insert")
def barrel_picker_before_insert(mapper, connect, target) -> None:
    clean_barrel_picker_data(target)
    result = connect.execute(
        sa.text("SELECT COALESCE(MAX(user_num), 0) FROM barrel_picker WHERE user_id = :uid"),
        {"uid": target.user_id},
    )
    db_max = result.scalar()
    session = OrmSession.object_session(target)
    pending_max = (
        max(
            (
                obj.user_num
                for obj in session.new
                if isinstance(obj, BarrelPicker)
                and obj.user_id == target.user_id
                and obj is not target
                and obj.user_num is not None
            ),
            default=0,
        )
        if session is not None
        else 0
    )
    target.user_num = max(db_max, pending_max) + 1


@event.listens_for(BarrelPicker, "before_update")
def barrel_picker_before_update(mapper, connect, target) -> None:
    clean_barrel_picker_data(target)


def clean_barrel_picker_data(target) -> None:
    target.name = target.name.strip()
    if target.description:
        target.description = target.description.strip()
    if target.url:
        target.url = target.url.strip()
