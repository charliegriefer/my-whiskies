import uuid
from typing import TYPE_CHECKING, List, Optional

from mywhiskies.extensions import db
from sqlalchemy import String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from mywhiskies.models import Bottle, User


class Bottler(db.Model):
    __tablename__ = "bottler"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(65))
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


@event.listens_for(Bottler, "before_update")
def bottle_before_update(mapper, connect, target) -> None:
    clean_bottler_data(target)


def clean_bottler_data(target) -> None:
    target.name = target.name.strip()
    target.description = target.description.strip() if target.description else None
    target.url = target.url.strip() if target.url else None
