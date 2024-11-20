import decimal
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Numeric, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mywhiskies.blueprints.core.models import bottle_distillery  # noqa: F401
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

if TYPE_CHECKING:  # avoid circular imports
    from mywhiskies.blueprints.bottler.models import Bottler
    from mywhiskies.blueprints.distillery.models import Distillery


class BottleTypes(enum.Enum):
    american_whiskey = "American Whiskey"
    bourbon = "Bourbon"
    canadian_whiskey = "Canadian Whiskey"
    irish_whiskey = "Irish Whiskey"
    rye = "Rye"
    scotch = "Scotch"
    world_whiskey = "World Whisk(e)y"
    other = "Other"


class Bottle(db.Model):
    __tablename__ = "bottle"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    date_created: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[BottleTypes]
    abv: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(6, 4))
    size: Mapped[Optional[int]]
    year_barrelled: Mapped[Optional[int]]
    year_bottled: Mapped[Optional[int]]
    url: Mapped[Optional[str]] = mapped_column(String(140))
    description: Mapped[Optional[str]] = mapped_column(Text)
    review: Mapped[Optional[str]] = mapped_column(Text)
    stars: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(2, 1))
    cost: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(8, 2))
    date_purchased: Mapped[Optional[datetime]]
    date_opened: Mapped[Optional[datetime]]
    date_killed: Mapped[Optional[datetime]]
    image_count: Mapped[int] = mapped_column(default=0)
    is_private: Mapped[bool] = mapped_column(
        default=False, server_default=sa.text("false"), nullable=False
    )
    personal_note: Mapped[Optional[str]] = mapped_column(Text)

    # foreign keys
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))
    bottler_id: Mapped[Optional[str]] = mapped_column(ForeignKey("bottler.id"))

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="bottles", lazy="select")

    distilleries: Mapped[List["Distillery"]] = relationship(
        "Distillery",
        secondary="bottle_distillery",
        order_by="Distillery.name",
    )
    bottler: Mapped["Bottler"] = relationship(
        foreign_keys=[bottler_id], back_populates="bottles"
    )


@event.listens_for(Bottle, "before_insert")
def bottle_before_insert(mapper, connect, target):
    clean_bottle_data(target)


@event.listens_for(Bottle, "before_update")
def bottle_before_update(mapper, connect, target):
    clean_bottle_data(target)


def clean_bottle_data(target):
    target.name = target.name.strip()
    target.size = target.size if target.size else None
    target.year_barrelled = target.year_barrelled if target.year_barrelled else None
    target.year_bottled = target.year_bottled if target.year_bottled else None
    target.url = target.url.strip() if target.url else None
    target.description = target.description.strip() if target.description else None
    target.review = target.review.strip() if target.review else None
    target.stars = target.stars if target.stars else None
