import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

if TYPE_CHECKING:
    from mywhiskies.blueprints.bottle.models import Bottle


class Distillery(db.Model):
    __tablename__ = "distillery"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
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
def clean_distillery_data(mapper, connect, target):
    target.name = target.name.strip()
    target.region_1 = target.region_1.strip()
    target.region_2 = target.region_2.strip()
    if target.description:
        target.description = target.description.strip()
    if target.url:
        target.url = target.url.strip()
