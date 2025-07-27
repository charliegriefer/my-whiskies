from mywhiskies.blueprints.auth.forms import ResendRegEmailForm
from mywhiskies.models import User
from werkzeug.datastructures import MultiDict


def test_resend_reg_email_form_valid(test_user_01: User) -> None:
    formdata = MultiDict({"email": test_user_01.email})
    form = ResendRegEmailForm(formdata)
    assert form.validate()


def test_resend_reg_email_form_invalid() -> None:
    formdata = MultiDict({"email": "not a valid email"})
    form = ResendRegEmailForm(formdata)
    assert not form.validate()
    assert "Invalid email address." in form.errors["email"]
