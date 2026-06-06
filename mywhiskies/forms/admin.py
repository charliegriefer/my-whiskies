from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class AddUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Temporary Password", validators=[DataRequired(), Length(min=8)])
    pre_verified = BooleanField("Mark email as pre-verified", default=True)
    submit = SubmitField("Add User")
