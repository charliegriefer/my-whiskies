from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import ResetPasswordRequestForm


def test_reset_password_request_form_valid(app, test_user):
    formdata = MultiDict(
        {
            "email": test_user.email,
        }
    )
    form = ResetPasswordRequestForm(formdata)
    foo = form.validate()
    print(form.errors)
    assert foo


def test_reset_password_request_form_invalid_email(app):
    formdata = MultiDict(
        {
            "email": "invalid-email",
        }
    )
    form = ResetPasswordRequestForm(formdata)
    assert not form.validate()
    assert "email" in form.errors
