import datetime

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import URL, InputRequired, Length, NumberRange, Optional

from .widgets import Select2Field

IMG_MESSAGE = "Permitted file types: jpg/jpeg, png"


def get_current_year() -> int:
    return datetime.date.today().year


class BottleAddForm(FlaskForm):
    name = TextAreaField(
        "Name:",
        validators=[InputRequired(), Length(max=100)],
        render_kw={"placeholder": "Name"},
    )
    url = StringField(
        "URL:",
        validators=[
            Length(max=140),
            URL(message="Please Enter a Valid URL"),
            Optional(),
        ],
        render_kw={"placeholder": "URL"},
    )
    type = SelectField("Bottle Type:", validators=[InputRequired()])
    distilleries = Select2Field(
        "Distilleries",
        choices=[],
        validators=[InputRequired()],
        render_kw={"placeholder": " Choose One or More Distilleries"},
    )
    bottler_id = SelectField("Bottler:")
    size = IntegerField(
        "Size (ml):",
        default=750,
        validators=[
            Optional(),
            NumberRange(min=0, max=2000, message="Size must not exceed 2000."),
        ],
        render_kw={"placeholder": "Size (ml)"},
    )
    year_barrelled = IntegerField(
        "Year Barrelled:",
        validators=[
            Optional(),
            NumberRange(
                min=1900,
                max=get_current_year(),
                message=f"Year Barrlled must be between 1900 and {get_current_year()}.",
            ),
        ],
        render_kw={"placeholder": "Year Barrelled"},
    )
    year_bottled = IntegerField(
        "Year Bottled:",
        validators=[
            Optional(),
            NumberRange(
                min=1900,
                max=get_current_year(),
                message=f"Year Bottled must be between 1900 and {get_current_year()}.",
            ),
        ],
        render_kw={"placeholder": "Year Bottled"},
    )
    abv = DecimalField(
        "ABV:",
        places=2,
        validators=[
            Optional(),
            NumberRange(min=30, max=90, message="Invalid value for ABV"),
        ],
        render_kw={"placeholder": "00.00"},
    )

    is_private = BooleanField("Private Bottle?")
    cost = DecimalField(
        "Cost:",
        places=2,
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "00.00"},
    )
    stars = SelectField("Stars:", validators=[Optional()], validate_choice=False)

    description = TextAreaField("Description:", validators=[Length(0, 65000)])
    personal_note = TextAreaField("Personal Note:", validators=[Length(0, 65000)])
    review = TextAreaField("Review:", validators=[Length(0, 65000)])

    date_purchased = DateField("Date Purchased:", validators=[Optional()])
    date_opened = DateField("Date Opened:", validators=[Optional()])
    date_killed = DateField("Date Killed:", validators=[Optional()])

    bottle_image_1 = FileField(
        "Image 1:", validators=[FileAllowed(["jpg", "jpeg", "png"], IMG_MESSAGE)]
    )
    bottle_image_2 = FileField(
        "Image 2:", validators=[FileAllowed(["jpg", "jpeg", "png"], IMG_MESSAGE)]
    )
    bottle_image_3 = FileField(
        "Image 3:", validators=[FileAllowed(["jpg", "jpeg", "png"], IMG_MESSAGE)]
    )

    submit = SubmitField("Add Bottle")


class BottleEditForm(BottleAddForm):
    remove_image_1 = HiddenField()
    remove_image_2 = HiddenField()
    remove_image_3 = HiddenField()
    submit = SubmitField("Edit Bottle")
