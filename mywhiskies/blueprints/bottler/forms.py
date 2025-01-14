from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import URL, InputRequired, Length, Optional


class BottlerAddForm(FlaskForm):
    name = StringField(
        "Name:",
        validators=[InputRequired("Bottler Name is required."), Length(1, 65)],
        render_kw={"placeholder": "Name"},
    )
    description = TextAreaField(
        "Description:",
        validators=[Length(max=65000)],
        render_kw={"placeholder": "Description"},
    )
    region_1 = StringField(
        "Location 1:",
        validators=[InputRequired("Location 1 is required."), Length(max=36)],
        render_kw={"placeholder": "Location 1"},
    )
    region_2 = StringField(
        "Location 2:",
        validators=[InputRequired("Location 2 is required."), Length(max=36)],
        render_kw={"placeholder": "Location 2"},
    )
    url = StringField(
        "URL:",
        validators=[Length(max=64), URL(message="Invalid URL"), Optional()],
        render_kw={"placeholder": "URL"},
    )
    submit = SubmitField("Add Bottler")


class BottlerEditForm(BottlerAddForm):
    submit = SubmitField("Edit Bottler")
