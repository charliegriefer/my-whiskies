from sqlalchemy import Column, ForeignKey

from mywhiskies.extensions import db

# Don't need a class here. This is an association table and should never be queried directly.
bottle_distillery = db.Table(
    "bottle_distillery",
    Column("bottle_id", ForeignKey("bottle.id"), primary_key=True),
    Column("distillery_id", ForeignKey("distillery.id"), primary_key=True),
)

bottle_barrel_picker = db.Table(
    "bottle_barrel_picker",
    Column("bottle_id", ForeignKey("bottle.id"), primary_key=True),
    Column("barrel_picker_id", ForeignKey("barrel_picker.id"), primary_key=True),
)
