import re

import requests
from flask import current_app, request
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import Email, EqualTo, InputRequired, Length, ValidationError

from mywhiskies.blueprints.user.models import User

USERNAME_DESCRIPTION = (
    "Username requirements:<ul>"
    "<li>Must be between 4 and 24 characters.</li>"
    "<li>Valid special characters: - _ @ ! ^ * $</li>"
    "<li>Spaces are not allowed.</li></ul>"
)

PW_DESCRIPTION = (
    "Password requirements:<ul>"
    "<li>Must be between 8 and 22 characters.</li>"
    "<li>Must contain at least one uppercase letter, one lowercase letter, and one digit.</li>"
    "<li>Spaces are not allowed.</li></ul>"
)

REG_CAPTCHA_MESSAGE = (
    "There was an issue processing your registration. Please try again later."
    "<br />If this problem persists, please contact us us at "
    '<a href="mailto:bartender@my-whiskies.online">bartender@my-whiskies.online</a>.'
)

RESET_CAPTCHA_MESSAGE = (
    "There was an issue processing your request. Please try again later."
    "<br />If this problem persists, please contact us us at "
    '<a href="mailto:bartender@my-whiskies.online">bartender@my-whiskies.online</a>.'
)


class PasswordValidatorMixin:
    def validate_password(self, password: StringField) -> None:
        regex = [r"[A-Z]", r"[a-z]", r"[0-9]"]
        is_valid_pw = all(re.search(r, password.data) for r in regex) and not re.search(
            r"\s", password.data
        )
        if password.data != self.password and not is_valid_pw:
            raise ValidationError("Password is invalid.")


class ReCaptchaV3:
    def __init__(self, action="form", threshold=0.5):
        self.action = action
        self.threshold = threshold

    def __call__(self, form, field):
        # bypass recaptcha validation during tests
        if current_app.config.get("TESTING"):
            field.data = 1.0
            return

        recaptcha_response = request.form.get("g-recaptcha-response")

        error_msg = ""
        if form.form_name.data == "reset_pw_request":
            error_msg = RESET_CAPTCHA_MESSAGE
        elif form.form_name.data == "registration":
            error_msg = REG_CAPTCHA_MESSAGE

        if not recaptcha_response:
            raise ValidationError(
                error_msg
            )  # TODO: differentiate between missing and invalid recaptcha

        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            timeout=5,
            data={
                "secret": current_app.config["RECAPTCHA_PRIVATE_KEY"],
                "response": recaptcha_response,
                "remoteip": request.remote_addr,
            },
        )
        result = r.json()

        if not result.get("success"):
            raise ValidationError(
                error_msg
            )  # TODO: differentiate between missing and invalid recaptcha

        score = result.get("score", 0)
        if score < self.threshold:
            raise ValidationError(
                error_msg
            )  # TODO: differentiate between missing and invalid recaptcha

        field.data = score


class LoginForm(FlaskForm):
    username = StringField(
        "Username:", validators=[InputRequired()], render_kw={"placeholder": "Username"}
    )
    password = PasswordField(
        "Password:", validators=[InputRequired()], render_kw={"placeholder": "Password"}
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")


class ResetPasswordRequestForm(FlaskForm):
    form_name = HiddenField("form_name", default="reset_pw_request")
    email = EmailField(
        "Email Address:",
        validators=[InputRequired(), Email(message="Enter a valid e-mail address.")],
        render_kw={"placeholder": "E-Mail Address"},
    )
    recaptcha = SubmitField(validators=[ReCaptchaV3(action="submit", threshold=0.5)])
    submit = SubmitField("Submit")


class ResetPWForm(PasswordValidatorMixin, FlaskForm):
    password = PasswordField(
        "Password:",
        validators=[InputRequired(), Length(min=8, max=24)],
        render_kw={"placeholder": "Password"},
        description=PW_DESCRIPTION,
    )
    password2 = PasswordField(
        "Repeat Password:",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )
    submit = SubmitField("Reset My Password ")


class RegistrationForm(PasswordValidatorMixin, FlaskForm):
    form_name = HiddenField("form_name", default="registration")
    username = StringField(
        "Username:",
        validators=[InputRequired(), Length(min=4, max=24)],
        render_kw={"placeholder": "Username"},
        description=USERNAME_DESCRIPTION,
    )
    email = StringField(
        "Email Address:",
        validators=[InputRequired(), Email()],
        render_kw={"placeholder": "Email Address"},
    )
    password = PasswordField(
        "Password:",
        validators=[InputRequired(), Length(min=8, max=24)],
        render_kw={"placeholder": "Password"},
        description=PW_DESCRIPTION,
    )
    password2 = PasswordField(
        "Repeat Password:",
        validators=[
            InputRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )
    agree_terms = BooleanField("", validators=[InputRequired()])
    recaptcha = SubmitField(validators=[ReCaptchaV3(action="submit", threshold=0.5)])
    submit = SubmitField("Register")

    def validate_username(self, username: StringField) -> None:
        error_message = ""
        m = re.compile(r"[a-zA-Z0-9-_@!^*$]*$")
        if not m.match(username.data):
            error_message = "Username is invalid."
        if User.query.filter_by(username=username.data).first():
            error_message = (
                f'"{username.data}" is unavailable. Please choose a different username.'
            )

        if username.data != self.username and len(error_message):
            raise ValidationError(error_message)

    def validate_email(self, email: StringField) -> None:
        if email.data != self.email and User.query.filter_by(email=email.data).first():
            raise ValidationError("Please use a different email address.")


class ResendRegEmailForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    submit = SubmitField("Resend Verification E-Mail")
