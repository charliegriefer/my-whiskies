import uuid
from datetime import datetime
from time import time
from typing import TYPE_CHECKING, List, Optional

import jwt
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from mywhiskies.extensions import db, login_manager

if TYPE_CHECKING:  # avoid circular imports
    from mywhiskies.blueprints.bottle.models import Bottle
    from mywhiskies.blueprints.bottler.models import Bottler
    from mywhiskies.blueprints.distillery.models import Distillery


class User(UserMixin, db.Model):
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    date_registered: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    email_confirmed: Mapped[bool] = mapped_column(default=False)
    email_confirm_date: Mapped[Optional[datetime]]
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_date: Mapped[Optional[datetime]]

    # relationships
    distilleries: Mapped[List["Distillery"]] = relationship(
        "Distillery", back_populates="user"
    )
    bottlers: Mapped[List["Bottler"]] = relationship("Bottler", back_populates="user")
    bottles: Mapped[List["Bottle"]] = relationship(
        "Bottle", back_populates="user", lazy="select"
    )

    def get_mail_confirm_token(self, expires_in: int = 600) -> str:
        payload = {"confirm_reg": self.id, "exp": time() + expires_in}
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_mail_confirm_token(token):
        try:
            decoded = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
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
            decoded = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user_id = decoded["reset_password"]
            user = db.get_or_404(User, user_id)
            return user
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
            # TODO: add some logging here!
            return None


class UserLogin(db.Model):
    __tablename__ = "user_login"
    user_id: Mapped[str] = mapped_column(db.ForeignKey("user.id"), primary_key=True)
    login_date: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, primary_key=True
    )
    ip_address: Mapped[str] = mapped_column(String(15))


@login_manager.user_loader
def load_user(user_id: str) -> User:
    return db.get_or_404(User, user_id)
