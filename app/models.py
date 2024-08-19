import enum
import uuid
from datetime import datetime
from time import time
from typing import List

import jwt
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import String, event
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class BottleTypes(enum.Enum):
    # pylint: disable=C0103
    american_whiskey = "American Whiskey"
    bourbon = "Bourbon"
    canadian_whiskey = "Canadian Whiskey"
    irish_whiskey = "Irish Whiskey"
    rye = "Rye"
    scotch = "Scotch"
    world_whiskey = "World Whisk(e)y"
    other = "Other"


bottle_distillery = db.Table(
    "bottle_distillery",
    db.Column("bottle_id", db.String(36), db.ForeignKey("bottle.id"), nullable=False),
    db.Column("distillery_id", db.String(36), db.ForeignKey("distillery.id"), nullable=False),
)


class Bottle(db.Model):
    __tablename__ = "bottle"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid.uuid4)
    date_created: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type = db.Column(db.Enum(BottleTypes))
    abv = db.Column(db.Float)
    size = db.Column(db.Integer)
    year_barrelled = db.Column(db.Integer, nullable=True)
    year_bottled = db.Column(db.Integer, nullable=True)
    url = db.Column(db.String(140))
    description = db.Column(db.Text, nullable=True)
    review = db.Column(db.Text, nullable=True)
    stars = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    date_purchased = db.Column(db.DateTime, nullable=True)
    date_opened = db.Column(db.DateTime, nullable=True)
    date_killed = db.Column(db.DateTime, nullable=True)
    image_count = db.Column(db.Integer, default=0)

    bottler_id = db.Column(db.String(36), db.ForeignKey("bottler.id"), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)

    distilleries: Mapped[List["Distillery"]] = db.relationship(secondary="bottle_distillery",
                                                               order_by="Distillery.name")

    bottler = db.relationship("Bottler", foreign_keys=[bottler_id])
    user = db.relationship("User", back_populates="bottles")


class Distillery(db.Model):
    __tablename__ = "distillery"
    id = db.Column(db.String(36), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(65), nullable=False)
    description = db.Column(db.Text, nullable=True)
    region_1 = db.Column(db.String(36), nullable=False)
    region_2 = db.Column(db.String(36), nullable=False)
    url = db.Column(db.String(64))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"))
    user = db.relationship("User", back_populates="distilleries")
    bottles = db.relationship("Bottle", secondary="bottle_distillery", back_populates="distilleries")


class Bottler(db.Model):
    __tablename__ = "bottler"
    id = db.Column(db.String(36), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(65), nullable=False)
    description = db.Column(db.Text, nullable=True)
    region_1 = db.Column(db.String(36), nullable=False)
    region_2 = db.Column(db.String(36), nullable=False)
    url = db.Column(db.String(64))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"))
    user = db.relationship("User", back_populates="bottlers")
    bottles = db.relationship("Bottle", back_populates="bottler")


class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    date_registered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email_confirmed = db.Column(db.Boolean(), nullable=False, default=False)
    email_confirm_date = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    deleted_date = db.Column(db.DateTime, nullable=True)
    distilleries = db.relationship("Distillery", back_populates="user")
    bottlers = db.relationship("Bottler", back_populates="user")
    bottles = db.relationship("Bottle", back_populates="user")

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
            # TODO: add some logging here! # pylint: disable=W0511
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
            # TODO: add some logging here! # pylint: disable=W0511
            return None


@login_manager.user_loader
def load_user(user_id: str) -> User:
    user = db.get_or_404(User, user_id)
    return user


# pylint: disable=W0613
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
