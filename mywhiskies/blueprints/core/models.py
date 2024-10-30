from sqlalchemy import Column, ForeignKey

from mywhiskies.extensions import db

# Don't need a class here. This is an association table and should never be queried directly.
bottle_distillery = db.Table(
    "bottle_distillery",
    Column("bottle_id", ForeignKey("bottle.id"), primary_key=True),
    Column("distillery_id", ForeignKey("distillery.id"), primary_key=True),
)
