import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

if TYPE_CHECKING:  # avoid circular imports
    from mywhiskies.blueprints.bottle.models import Bottle


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
