import decimal
import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Numeric, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mywhiskies.extensions import db
from mywhiskies.models.core import bottle_distillery  # noqa: F401

if TYPE_CHECKING:
    from mywhiskies.models import Bottler, Distillery, User


class BottleTypes(enum.Enum):
    AMERICAN_SINGLE_MALT = "American Single Malt"
    AMERICAN_WHISKEY = "American Whiskey"
    BOURBON = "Bourbon"
    CANADIAN_WHISKEY = "Canadian Whiskey"
    IRISH_WHISKEY = "Irish Whiskey"
    RYE = "Rye"
    SCOTCH = "Scotch"
    TENNESSEE_WHISKEY = "Tennessee Whiskey"
    WORLD_WHISKEY = "World Whisk(e)y"
    OTHER = "Other"


class BottleImage(db.Model):
    __tablename__ = "bottle_image"
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    bottle_id: Mapped[str] = mapped_column(ForeignKey("bottle.id"))
    sequence: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    bottle: Mapped["Bottle"] = relationship("Bottle", back_populates="images")

    __table_args__ = (
        sa.UniqueConstraint("bottle_id", "sequence", name="_bottle_sequence_uc"),
    )


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
    images: Mapped[List["BottleImage"]] = relationship(
        "BottleImage",
        back_populates="bottle",
        order_by="BottleImage.sequence",
        cascade="all, delete-orphan",
    )

    @property
    def image_count(self) -> int:
        """Return the number of images associated with this bottle"""
        return len(self.images)

    @property
    def next_available_sequence(self) -> int:
        """Return the next available sequence number (1-3)"""
        used_sequences = {img.sequence for img in self.images}
        return min(seq for seq in range(1, 4) if seq not in used_sequences)

    def get_image_by_sequence(self, sequence: int) -> Optional[BottleImage]:
        """Get image by sequence number"""
        return next((img for img in self.images if img.sequence == sequence), None)


@event.listens_for(Bottle, "before_insert")
def bottle_before_insert(mapper, connect, target) -> None:
    clean_bottle_data(target)


@event.listens_for(Bottle, "before_update")
def bottle_before_update(mapper, connect, target) -> None:
    clean_bottle_data(target)


def clean_bottle_data(target) -> None:
    target.name = target.name.strip()
    target.size = target.size if target.size else None
    target.year_barrelled = target.year_barrelled if target.year_barrelled else None
    target.year_bottled = target.year_bottled if target.year_bottled else None
    target.url = target.url.strip() if target.url else None
    target.description = target.description.strip() if target.description else None
    target.review = target.review.strip() if target.review else None
    target.stars = target.stars if target.stars else None
