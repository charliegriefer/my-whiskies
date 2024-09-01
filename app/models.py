import decimal
import enum
import uuid
from datetime import datetime
from time import time
from typing import List, Optional

import jwt
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import Column, ForeignKey, Numeric, String, Text, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class BottleTypes(enum.Enum):
    american_whiskey = "American Whiskey"
    bourbon = "Bourbon"
    canadian_whiskey = "Canadian Whiskey"
    irish_whiskey = "Irish Whiskey"
    rye = "Rye"
    scotch = "Scotch"
    world_whiskey = "World Whisk(e)y"
    other = "Other"


# Don't need a class here. This is an association table and should never be queried directly.
bottle_distillery = db.Table(
    "bottle_distillery",
    Column("bottle_id", ForeignKey("bottle.id"), primary_key=True),
    Column("distillery_id", ForeignKey("distillery.id"), primary_key=True)
)


class Bottle(db.Model):
    __tablename__ = "bottle"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
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

    # foreign keys
    bottler_id: Mapped[Optional[str]] = mapped_column(ForeignKey("bottler.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))

    # relationships
    user: Mapped["User"] = relationship(back_populates="bottles")
    distilleries: Mapped[List["Distillery"]] = relationship(secondary="bottle_distillery",
                                                            order_by="Distillery.name")
    bottler: Mapped["Bottler"] = relationship(foreign_keys=[bottler_id])


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
    bottles: Mapped[List["Bottle"]] = relationship(secondary="bottle_distillery", back_populates="distilleries")


class Bottler(db.Model):
    __tablename__ = "bottler"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
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


class User(UserMixin, db.Model):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    date_registered: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    email_confirmed: Mapped[bool] = mapped_column(default=False)
    email_confirm_date: Mapped[Optional[datetime]]
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_date: Mapped[Optional[datetime]]

    # relationships
    distilleries: Mapped[List["Distillery"]] = relationship(back_populates="user")
    bottlers: Mapped[List["Bottler"]] = relationship(back_populates="user")
    bottles: Mapped[List["Bottle"]] = relationship(back_populates="user")

    def get_mail_confirm_token(self, expires_in: int = 600) -> str:
        payload = {"confirm_reg": self.id, "exp": time() + expires_in}
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_mail_confirm_token(token):
        try:
            decoded = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user_id = decoded["confirm_reg"]
            user = db.get_or_404(User, user_id)
            return user
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
            # TODO: add some logging here!
            return None

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        payload = {"reset_password": self.id, "exp": time() + expires_in}
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token: str):
        try:
            decoded = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user_id = decoded["reset_password"]
            user = db.get_or_404(User, user_id)
            return user
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
            # TODO: add some logging here!
            return None


@login_manager.user_loader
def load_user(user_id: str) -> User:
    user = db.get_or_404(User, user_id)
    return user


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


@event.listens_for(Distillery, "before_insert")
def clean_distillery_data(mapper, connect, target):
    target.name = target.name.strip()
    target.region_1 = target.region_1.strip()
    target.region_2 = target.region_2.strip()
    if target.description:
        target.description = target.description.strip()
    if target.url:
        target.url = target.url.strip()
