import uuid
from datetime import datetime, timezone
from time import time
from typing import TYPE_CHECKING, List, Optional

import jwt
from flask import current_app
from flask_login import UserMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from mywhiskies.extensions import db, login_manager

if TYPE_CHECKING:
    from mywhiskies.models import BarrelPicker, Bottle, Bottler, Distillery


class PasskeyCredential(db.Model):
    __tablename__ = "passkey_credential"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(db.ForeignKey("user.id"), nullable=False)
    credential_id: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    public_key: Mapped[bytes] = mapped_column(db.LargeBinary, nullable=False)
    sign_count: Mapped[int] = mapped_column(default=0)
    nickname: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="passkeys")


class User(UserMixin, db.Model):
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(120), index=True, unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    date_registered: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    email_confirmed: Mapped[bool] = mapped_column(default=False)
    email_confirm_date: Mapped[Optional[datetime]]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_pro: Mapped[bool] = mapped_column(default=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_private: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_date: Mapped[Optional[datetime]]
    last_login_at: Mapped[Optional[datetime]]
    warned_at: Mapped[Optional[datetime]]

    # relationships
    distilleries: Mapped[List["Distillery"]] = relationship("Distillery", back_populates="user")
    bottlers: Mapped[List["Bottler"]] = relationship("Bottler", back_populates="user")
    barrel_pickers: Mapped[List["BarrelPicker"]] = relationship("BarrelPicker", back_populates="user")
    bottles: Mapped[List["Bottle"]] = relationship("Bottle", back_populates="user", lazy="select")
    logins: Mapped[List["UserLogin"]] = relationship("UserLogin", back_populates="user", lazy="select")
    passkeys: Mapped[List["PasskeyCredential"]] = relationship(
        "PasskeyCredential", back_populates="user", lazy="select"
    )

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

    def get_email_change_token(self, new_email: str, expires_in: int = 3600) -> str:
        payload = {"change_email": self.id, "new_email": new_email, "exp": time() + expires_in}
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_email_change_token(token: str):
        try:
            decoded = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user_id = decoded["change_email"]
            new_email = decoded["new_email"]
            user = db.get_or_404(User, user_id)
            return user, new_email
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError, KeyError):
            return None, None


class UserLogin(db.Model):
    __tablename__ = "user_login"
    user_id: Mapped[str] = mapped_column(db.ForeignKey("user.id"), primary_key=True)
    login_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45))

    user: Mapped["User"] = relationship("User", back_populates="logins")


@login_manager.user_loader
def load_user(user_id: str) -> User:
    return db.get_or_404(User, user_id)
