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
    ValidationError,
)
from wtforms.validators import URL, InputRequired, Length, NumberRange, Optional

from .widgets import Select2Field

IMG_MESSAGE = "Permitted file types: jpg/jpeg, png"


def get_current_year() -> int:
    return datetime.date.today().year


def validate_bottle_purchased_date(form, field):
    if field.data and field.data > datetime.date.today():
        raise ValidationError("Date Purchased cannot be in the future.")


def validate_bottle_opened_date(form, field):
    if (
        field.data
        and form.date_purchased.data
        and field.data < form.date_purchased.data
    ):
        raise ValidationError("Date Opened cannot precede Date Purchased.")


def validate_bottle_killed_date(form, field):
    if field.data and form.date_opened.data and field.data < form.date_opened.data:
        raise ValidationError("Date Killed cannot precede Date Opened.")
    if field.data > datetime.date.today():
        raise ValidationError("Date Killed cannot be in the future.")


def validate_year_bottled_date(form, field):
    if (
        field.data
        and form.year_barrelled.data
        and field.data < form.year_barrelled.data
    ):
        raise ValidationError("Year Bottled cannot precede Year Barrelled.")


class BottleAddForm(FlaskForm):
    name = TextAreaField(
        "Name:",
        validators=[InputRequired("Bottle name is required."), Length(max=100)],
        render_kw={"placeholder": "Name"},
    )
    url = StringField(
        "URL:",
        validators=[
            Length(max=140),
            URL(message="Please enter a valid URL"),
            Optional(),
        ],
        render_kw={"placeholder": "URL"},
    )
    type = SelectField(
        "Bottle Type:", validators=[InputRequired("Bottle Type is required.")]
    )
    distilleries = Select2Field(
        "Distilleries",
        choices=[],
        validators=[InputRequired("Distilleries is required.")],
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
                message=f"Year Barrelled must be between 1900 and {get_current_year()}.",
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
            validate_year_bottled_date,
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
        validators=[
            Optional(),
            NumberRange(min=0, message="Cost must be greater than zero."),
        ],
        render_kw={"placeholder": "00.00"},
    )
    stars = SelectField("Stars:", validators=[Optional()], validate_choice=False)

    description = TextAreaField("Description:", validators=[Length(0, 65000)])
    personal_note = TextAreaField("Personal Note:", validators=[Length(0, 65000)])
    review = TextAreaField("Review:", validators=[Length(0, 65000)])

    date_purchased = DateField(
        "Date Purchased:", validators=[Optional(), validate_bottle_purchased_date]
    )
    date_opened = DateField(
        "Date Opened:", validators=[Optional(), validate_bottle_opened_date]
    )
    date_killed = DateField(
        "Date Killed:", validators=[Optional(), validate_bottle_killed_date]
    )

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
