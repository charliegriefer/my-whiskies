import uuid
from typing import TYPE_CHECKING, List, Optional

from mywhiskies.extensions import db
from sqlalchemy import ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from mywhiskies.models import Bottle, User


class Distillery(db.Model):
    __tablename__ = "distillery"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(65))
    description: Mapped[Optional[str]] = mapped_column(Text)
    region_1: Mapped[str] = mapped_column(String(36))
    region_2: Mapped[str] = mapped_column(String(36))
    url: Mapped[Optional[str]] = mapped_column(String(64))

    # foreign keys
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))

    # relationships
    user: Mapped["User"] = relationship(back_populates="distilleries")
    bottles: Mapped[List["Bottle"]] = relationship(
        "Bottle", secondary="bottle_distillery", back_populates="distilleries"
    )


@event.listens_for(Distillery, "before_insert")
def distillery_before_insert(mapper, connect, target) -> None:
    clean_distillery_data(target)


@event.listens_for(Distillery, "before_update")
def distillery_before_update(mapper, connect, target) -> None:
    clean_distillery_data(target)


def clean_distillery_data(target) -> None:
    target.name = target.name.strip()
    target.region_1 = target.region_1.strip()
    target.region_2 = target.region_2.strip()
    if target.description:
        target.description = target.description.strip()
    if target.url:
        target.url = target.url.strip()
