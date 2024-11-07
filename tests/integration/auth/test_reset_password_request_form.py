from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import ResetPasswordRequestForm
from mywhiskies.blueprints.user.models import User


def test_reset_password_request_form_valid(test_user: User) -> None:
    formdata = MultiDict({"email": test_user.email})
    form = ResetPasswordRequestForm(formdata)
    assert form.validate()


def test_reset_password_request_form_invalid_email() -> None:
    formdata = MultiDict({"email": "invalid-email"})
    form = ResetPasswordRequestForm(formdata)
    assert not form.validate()
    assert "email" in form.errors
