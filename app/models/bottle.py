import enum
import uuid

from datetime import datetime

from app.extensions import db


class BottleTypes(enum.Enum):
    scotch = "Scotch"
    bourbon = "Bourbon"
    rye = "Rye"
    american_whiskey = "American Whiskey"
    world_whiskey = "World Whisk(e)y"
    other = "Other"


class Distillery(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(65), nullable=False)
    description = db.Column(db.Text, nullable=True)
    region_1 = db.Column(db.String(36), nullable=False)
    region_2 = db.Column(db.String(36), nullable=False)
    url = db.Column(db.String(64))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"))
    bottles = db.relationship("Bottle", backref="distillery")


class Bottle(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=uuid.uuid4)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.Enum(BottleTypes))
    year = db.Column(db.Integer)
    abv = db.Column(db.Float)
    url = db.Column(db.String(64))
    description = db.Column(db.Text, nullable=True)
    review = db.Column(db.Text, nullable=True)
    stars = db.Column(db.Float, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    date_purchased = db.Column(db.DateTime, nullable=True)
    date_killed = db.Column(db.DateTime, nullable=True)
    has_image = db.Column(db.Boolean, default=False)
    distillery_id = db.Column(db.String(36), db.ForeignKey("distillery.id"), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
