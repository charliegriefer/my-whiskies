import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models.user import User

pw_description = "Password requirements:<ul>"
pw_description += "<li>Must be between 8 and 22 characters.</li>"
pw_description += "<li>Must contain at least one uppercase letter, one lowercase letter, and one digit.</li>"
pw_description += "<li>Spaces are not allowed.</li></ul>"


class LoginForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField("Password:", validators=[DataRequired()], render_kw={"placeholder": "Password"})
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email Address:",
                        validators=[DataRequired(), Email(message="Enter a valid e-mail address.")],
                        render_kw={"placeholder": "E-Mail Address"},)
    submit = SubmitField("Submit")


class ResetPWForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Reset My Password ")


class RegistrationForm(FlaskForm):
    username = StringField("Username:", validators=[DataRequired()], render_kw={"placeholder": "Username"})
    email = StringField("Email Address:",
                        validators=[DataRequired(), Email()],
                        render_kw={"placeholder": "Email Address"})
    password = PasswordField("Password:",
                             validators=[DataRequired(), Length(min=8, max=22)],
                             render_kw={"placeholder": "Password"},
                             description=pw_description)
    password2 = PasswordField("Repeat Password:",
                              validators=[DataRequired(), EqualTo("password", message="Passwords do not match.")],
                              render_kw={"placeholder": "Repeat Password"})
    submit = SubmitField("Register")

    def validate_username(self, username: StringField) -> None:
        if username.data != self.username and User.query.filter_by(username=username.data).first():
            raise ValidationError("Please use a different username.")

    def validate_password(self, password: StringField) -> None:
        if password.data != self.password:
            valid = True

            if re.search("[0-9]", password.data) is None:
                valid = False
            if re.search("[A-Z]", password.data) is None:
                valid = False
            if re.search("[a-z]", password.data) is None:
                valid = False
            if " " in password.data:
                valid = False
            if not valid:
                raise ValidationError("Password is invalid.")

    def validate_email(self, email: StringField) -> None:
        if email.data != self.email and User.query.filter_by(email=email.data).first():
            raise ValidationError("Please use a different email address.")


class ResendRegEmailForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Resend Verification E-Mail")
