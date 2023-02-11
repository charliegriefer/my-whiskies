import uuid
from datetime import datetime
from time import time

import jwt

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


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

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def get_mail_confirm_token(self, expires_in: int = 600) -> str:
        payload = {"confirm_reg": self.id, "exp": time() + expires_in}
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_mail_confirm_token(token):
        try:
            decoded = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            id = decoded["confirm_reg"]
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
            # TODO: add some logging here!
            return None
        else:
            return User.query.get(id)

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
            id = decoded["reset_password"]
        except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
            # TODO: add some logging here!
            return None
        else:
            return User.query.get(id)


@login_manager.user_loader
def load_user(id: str) -> User:
    return User.query.get(id)
