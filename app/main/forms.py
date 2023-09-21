import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    DateField, DecimalField, HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
)
from wtforms.validators import InputRequired, Length, NumberRange, Optional, URL


def get_current_year() -> int:
    return datetime.date.today().year


img_message = "Permitted file types: jpg/jpeg, png"

class BottlerForm(FlaskForm):
    name = StringField("Name:", validators=[InputRequired(), Length(1, 65)], render_kw={"placeholder": "Name"})
    description = TextAreaField("Description:",
                                validators=[Length(max=65000)],
                                render_kw={"placeholder": "Description"})
    region_1 = StringField("Location 1:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 1"})
    region_2 = StringField("Location 2:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 2"})
    url = StringField("URL:",
                      validators=[Length(max=64), URL(message="Invalid URL"), Optional()],
                      render_kw={"placeholder": "URL"})
    submit = SubmitField("Add Bottler")


class DistilleryForm(FlaskForm):
    name = StringField("Name:", validators=[InputRequired(), Length(1, 65)], render_kw={"placeholder": "Name"})
    description = TextAreaField("Description:",
                                validators=[Length(max=65000)],
                                render_kw={"placeholder": "Description"})
    region_1 = StringField("Location 1:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 1"})
    region_2 = StringField("Location 2:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 2"})
    url = StringField("URL:",
                      validators=[Length(max=64), URL(message="Please Enter a Valid URL"), Optional()],
                      render_kw={"placeholder": "URL"})
    submit = SubmitField("Add Distillery")


class BottleForm(FlaskForm):
    name = TextAreaField("Name:",
                         validators=[InputRequired(),
                                     Length(max=100)],
                         render_kw={"placeholder": "Name"})
    url = StringField("URL:",
                      validators=[Length(max=100),
                                  URL(message="Please Enter a Valid URL"),
                                  Optional()],
                      render_kw={"placeholder": "URL"})
    type = SelectField("Bottle Type:", validators=[InputRequired()])
    distillery_id = SelectField("Distiller:", validators=[InputRequired()])
    bottler_id = SelectField("Bottler:")
    size = IntegerField("Size (ml):",
                        default=750,
                        validators=[Optional(),
                                    NumberRange(min=0,
                                                max=2000,
                                                message="Size must not exceed 2000.")],
                        render_kw={"placeholder": "Size (ml)"})
    year_barrelled = IntegerField("Year Barrelled:",
                                  validators=[Optional(),
                                  NumberRange(min=1900,
                                  max=get_current_year(),
                                  message=f"Year Barrlled must be between 1900 and {get_current_year()}.")],
                                  render_kw={"placeholder": "Year Barrelled"})
    year_bottled = IntegerField("Year Bottled:",
                                validators=[Optional(),
                                NumberRange(min=1900,
                                max=get_current_year(),
                                message=f"Year Bottled must be between 1900 and {get_current_year()}.")],
                                render_kw={"placeholder": "Year Bottled"})
    abv = DecimalField("ABV:",
                       places=2,
                       validators=[Optional(), NumberRange(min=30, max=90, message="Invalid value for ABV")],
                       render_kw={"placeholder": "00.00"})

    cost = DecimalField("Cost:", places=2, validators=[Optional(), NumberRange(min=0)], render_kw={"placeholder": "00.00"})
    stars = SelectField("Stars:", validators=[Optional()], validate_choice=False)

    description = TextAreaField("Description:", validators=[Length(0, 65000)])
    review = TextAreaField("Review:", validators=[Length(0, 65000)])

    date_purchased = DateField("Date Purchased:", validators=[Optional()])
    date_opened = DateField("Date Opened:", validators=[Optional()])
    date_killed = DateField("Date Killed:", validators=[Optional()])

    bottle_image_1 = FileField("Image 1:", validators=[FileAllowed(["jpg", "jpeg", "png"], img_message)])
    bottle_image_2 = FileField("Image 2:", validators=[FileAllowed(["jpg", "jpeg", "png"], img_message)])
    bottle_image_3 = FileField("Image 3:", validators=[FileAllowed(["jpg", "jpeg", "png"], img_message)])

    submit = SubmitField("Add Bottle")


class BottleEditForm(BottleForm):
    remove_image_1 = HiddenField()
    remove_image_2 = HiddenField()
    remove_image_3 = HiddenField()
    submit = SubmitField("Edit Bottle")


class DistilleryEditForm(FlaskForm):
    name = StringField("Name:", validators=[InputRequired(), Length(1, 65)], render_kw={"placeholder": "Name"})
    description = TextAreaField("Description:",
                                validators=[Length(max=65000)],
                                render_kw={"placeholder": "Description"})
    region_1 = StringField("Location 1:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 1"})
    region_2 = StringField("Location 2:",
                           validators=[InputRequired(), Length(max=36)],
                           render_kw={"placeholder": "Location 2"})
    url = StringField("URL:",
                      validators=[Length(max=64), URL(message="Please Enter a Valid URL"), Optional()],
                      render_kw={"placeholder": "URL"})
    submit = SubmitField("Edit Distillery")


class BottlerEditForm(BottlerForm):
    submit = SubmitField("Edit Bottler")
