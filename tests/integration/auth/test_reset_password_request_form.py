from werkzeug.datastructures import MultiDict

from mywhiskies.forms.auth import ResetPasswordRequestForm
from mywhiskies.models import User


def test_reset_password_request_form_valid(test_user_01: User) -> None:
    formdata = MultiDict({"email": test_user_01.email})
    form = ResetPasswordRequestForm(formdata)
    assert form.validate()


def test_reset_password_request_form_invalid_email() -> None:
    formdata = MultiDict({"email": "invalid-email"})
    form = ResetPasswordRequestForm(formdata)
    assert not form.validate()
    assert "email" in form.errors
