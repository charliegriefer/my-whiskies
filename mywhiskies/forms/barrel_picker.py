from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, URLField
from wtforms.validators import URL, InputRequired, Length, Optional


class BarrelPickerAddForm(FlaskForm):
    name = StringField(
        "Name:",
        validators=[InputRequired("Name is required."), Length(max=65)],
        render_kw={"placeholder": "Name"},
    )
    description = TextAreaField("Description:", validators=[Length(0, 65000)])
    url = URLField(
        "URL:",
        validators=[Length(max=64), URL(message="Please enter a valid URL"), Optional()],
        render_kw={"placeholder": "https://"},
    )
    submit = SubmitField("Add Barrel Picker")


class BarrelPickerEditForm(BarrelPickerAddForm):
    submit = SubmitField("Save Changes")
