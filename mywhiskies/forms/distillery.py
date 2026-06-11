from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import URL, InputRequired, Length, Optional


class DistilleryAddForm(FlaskForm):
    name = StringField(
        "Name:",
        validators=[InputRequired("Distillery name is required."), Length(1, 65)],
        render_kw={"placeholder": "Name"},
    )
    description = TextAreaField(
        "Description:",
        validators=[Length(max=65000)],
        render_kw={"placeholder": "Description"},
    )
    region_1 = StringField(
        "Location 1:",
        validators=[Optional(), Length(max=36)],
        render_kw={"placeholder": "Location 1"},
    )
    region_2 = StringField(
        "Location 2:",
        validators=[Optional(), Length(max=36)],
        render_kw={"placeholder": "Location 2"},
    )
    url = URLField(
        "URL:",
        validators=[
            Length(max=64),
            URL(message="Please enter a valid URL"),
            Optional(),
        ],
        render_kw={"placeholder": "URL"},
    )
    submit = SubmitField("Add Distillery")


class DistilleryEditForm(DistilleryAddForm):
    submit = SubmitField("Edit Distillery")


class DistilleryQuickAddForm(FlaskForm):
    name = StringField(
        "Name:",
        validators=[InputRequired("Distillery name is required."), Length(1, 65)],
        render_kw={"placeholder": "Name"},
    )
    region_1 = StringField(
        "Location 1:",
        validators=[Optional(), Length(max=36)],
        filters=(lambda x: x or "",),
        render_kw={"placeholder": "e.g. Bardstown"},
    )
    region_2 = StringField(
        "Location 2:",
        validators=[Optional(), Length(max=36)],
        filters=(lambda x: x or "",),
        render_kw={"placeholder": "e.g. KY"},
    )
    url = URLField(
        "URL:",
        validators=[Length(max=64), URL(message="Please enter a valid URL"), Optional()],
        render_kw={"placeholder": "https://"},
    )
    submit = SubmitField("Add Distillery")
