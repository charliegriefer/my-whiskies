from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, InputRequired

from mywhiskies.forms.auth import PasswordValidatorMixin


class ChangeEmailForm(FlaskForm):
    email = EmailField(
        "New E-Mail Address:",
        validators=[DataRequired("Please enter your new e-mail address."), Email()],
        render_kw={"placeholder": "New e-mail address"},
    )
    submit = SubmitField("Send Confirmation Email")


class ChangePasswordForm(PasswordValidatorMixin, FlaskForm):
    current_password = PasswordField(
        "Current Password:",
        validators=[InputRequired("Current password is required.")],
        render_kw={"placeholder": "Current password"},
    )
    password = PasswordField(
        "New Password:",
        validators=[InputRequired("New password is required.")],
        render_kw={"placeholder": "New password"},
    )
    password2 = PasswordField(
        "Confirm New Password:",
        validators=[
            InputRequired("Please confirm your new password."),
            EqualTo("password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Confirm new password"},
    )
    submit = SubmitField("Change Password")


class DeleteAccountForm(FlaskForm):
    confirm_username = StringField(
        "Type your username to confirm:",
        validators=[DataRequired("Please type your username to confirm.")],
        render_kw={"placeholder": "Your username"},
    )
    submit = SubmitField("Permanently Delete My Account")
