from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import ResendRegEmailForm
from mywhiskies.blueprints.user.models import User


def test_resend_reg_email_form_valid(test_user: User) -> None:
    formdata = MultiDict({"email": test_user.email})
    form = ResendRegEmailForm(formdata)
    assert form.validate()


def test_resend_reg_email_form_invalid(test_user: User) -> None:
    formdata = MultiDict({"email": "not a valid email"})
    form = ResendRegEmailForm(formdata)
    assert not form.validate()
    assert "Invalid email address." in form.errors["email"]
