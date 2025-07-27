import re

import requests
from flask import Markup, current_app, request, url_for
from flask_wtf import FlaskForm
from mywhiskies.models import User
from mywhiskies.services.auth.registration import find_user_by_email
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.fields import EmailField, Label
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    ValidationError,
)

USERNAME_DESCRIPTION = (
    "Username requirements:<ul>"
    "<li>Must be between 4 and 24 characters.</li>"
    "<li>Only letters, numbers, and underscore characters are allowed.</li>"
    "</ul>"
)

PW_DESCRIPTION = (
    "Password requirements:<ul>"
    "<li>Must be between 8 and 24 characters.</li>"
    "<li>Must contain at least one uppercase letter, one lowercase letter, and one digit.</li>"
    "<li>Spaces are not allowed.</li></ul>"
)

# TODO: break this out into individual messages for login, registration, etc.
CAPTCHA_MESSAGE = (
    "There was an issue processing your request. Please try again later."
    "<br />If this problem persists, please contact us us at "
    '<a href="mailto:bartender@my-whiskies.online">bartender@my-whiskies.online</a>.'
)

CAPTCHA_THRESHOLD = 0.5


class UsernameValidatorMixin:
    def validate_username(self, username: StringField) -> None:
        error_message = ""
        m = re.compile(r"[a-zA-Z0-9_]+$")
        if not m.match(username.data):
            error_message = "Username does not adhere to the specified requirements."
        if User.query.filter_by(username=username.data).first():
            error_message = (
                f'"{username.data}" is unavailable. Please choose a different username.'
            )
        if username.data != self.username and len(error_message):
            raise ValidationError(error_message)


class PasswordValidatorMixin:
    def validate_password(self, password: StringField) -> None:
        regex = [r"[A-Z]", r"[a-z]", r"[0-9]"]
        is_valid_pw = (
            8 <= len(password.data) <= 24
            and all(re.search(r, password.data) for r in regex)
            and not re.search(r"\s", password.data)
        )

        if not is_valid_pw:
            raise ValidationError("Password does not meet the defined requirements.")


class ReCaptchaV3:
    def __init__(self, action="form", threshold=CAPTCHA_THRESHOLD):
        self.action = action
        self.threshold = threshold

    def __call__(self, form, field):
        # bypass recaptcha validation during tests
        if current_app.config.get("TESTING"):
            field.data = 1.0
            return

        recaptcha_response = form.g_recaptcha_response.data

        error_msg = ""
        if form.form_name.data == "reset_pw_request":
            error_msg = CAPTCHA_MESSAGE
        elif form.form_name.data == "registration":
            error_msg = CAPTCHA_MESSAGE
        elif form.form_name.data == "login":
            error_msg = CAPTCHA_MESSAGE

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
    form_name = HiddenField("form_name", default="login")
    username = StringField(
        "Username:",
        validators=[InputRequired("Username is required.")],
        render_kw={"placeholder": "Username"},
    )
    password = PasswordField(
        "Password:",
        validators=[InputRequired("Password is required.")],
        render_kw={"placeholder": "Password"},
    )
    remember_me = BooleanField("Remember Me")
    g_recaptcha_response = HiddenField("", id="g-recaptcha-response")
    recaptcha = SubmitField(
        validators=[ReCaptchaV3(action="submit", threshold=CAPTCHA_THRESHOLD)]
    )
    submit = SubmitField("Log In")


class ResetPasswordRequestForm(FlaskForm):
    form_name = HiddenField("form_name", default="reset_password_request")
    g_recaptcha_response = HiddenField(
        "g-recaptcha-response", id="g-recaptcha-response"
    )
    email = EmailField(
        "Email Address:",
        validators=[
            InputRequired("Email address is required."),
            Email(message="Enter a valid e-mail address."),
        ],
        render_kw={"placeholder": "E-Mail Address"},
    )
    recaptcha = SubmitField(
        validators=[ReCaptchaV3(action="submit", threshold=CAPTCHA_THRESHOLD)]
    )
    submit = SubmitField("Submit")


class ResetPWForm(PasswordValidatorMixin, FlaskForm):
    form_name = HiddenField("form_name", default="reset_pw")
    g_recaptcha_response = HiddenField(
        "g-recaptcha-response", id="g-recaptcha-response"
    )
    password = PasswordField(
        "Password:",
        validators=[InputRequired("Password is required.")],
        render_kw={"placeholder": "Password"},
        description=PW_DESCRIPTION,
    )
    password2 = PasswordField(
        "Repeat Password:",
        validators=[
            InputRequired("Verifying the password is required."),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )
    recaptcha = SubmitField(
        validators=[ReCaptchaV3(action="submit", threshold=CAPTCHA_THRESHOLD)]
    )
    submit = SubmitField("Reset My Password ")


class RegistrationForm(UsernameValidatorMixin, PasswordValidatorMixin, FlaskForm):
    form_name = HiddenField("form_name", default="registration")
    username = StringField(
        "Username:",
        validators=[InputRequired("Username is required."), Length(min=4, max=24)],
        render_kw={"placeholder": "Username"},
        description=USERNAME_DESCRIPTION,
    )
    email = StringField(
        "Email Address:",
        validators=[
            InputRequired("Email address is required."),
            Email("Please enter a valid email address."),
        ],
        render_kw={"placeholder": "Email Address"},
    )
    password = PasswordField(
        "Password:",
        validators=[InputRequired("Password is required.")],
        render_kw={"placeholder": "Password"},
        description=PW_DESCRIPTION,
    )
    password2 = PasswordField(
        "Repeat Password:",
        validators=[
            InputRequired("Verifying the password is required."),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )
    agree_terms = BooleanField(
        "",
        validators=[DataRequired("You must agree to the Terms of Service.")],
    )
    g_recaptcha_response = HiddenField("", id="g-recaptcha-response")
    recaptcha = SubmitField(
        validators=[ReCaptchaV3(action="submit", threshold=CAPTCHA_THRESHOLD)]
    )
    submit = SubmitField("Register")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_terms_label()

    def set_terms_label(self) -> None:
        txt = Markup(
            f"I agree to the <a href=\"{url_for('core.terms')}\">Terms of Service</a>"
        )
        self.agree_terms.label = Label("agree_terms", txt)

    def validate_email(self, email: StringField) -> None:
        if email.data != self.email and find_user_by_email(email.data):
            raise ValidationError("This email address cannot be used.")


class ResendRegEmailForm(FlaskForm):
    form_name = HiddenField("form_name", default="resend_reg_email")
    email = StringField("Email", validators=[InputRequired(), Email()])
    g_recaptcha_response = HiddenField("", id="g-recaptcha-response")
    recaptcha = SubmitField(
        validators=[ReCaptchaV3(action="submit", threshold=CAPTCHA_THRESHOLD)]
    )
    submit = SubmitField("Resend Verification E-Mail")
