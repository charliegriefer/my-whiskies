from unittest.mock import patch

from werkzeug.datastructures import MultiDict

from mywhiskies.blueprints.auth.forms import RegistrationForm


def test_valid_registration_form(app):
    """Test that a valid form passes validation."""
    with app.app_context():
        with patch.object(RegistrationForm, "recaptcha", True):  # Mock ReCAPTCHA
            form = RegistrationForm(
                formdata=MultiDict(
                    {
                        "username": "validuser",
                        "email": "user@example.com",
                        "password": "StrongPassword123",
                        "password2": "StrongPassword123",
                        "agree_terms": True,
                    }
                )
            )
            assert form.validate(), f"Form validation failed: {form.errors}"


def test_invalid_email(app):
    """Test that an invalid email fails validation."""
    with app.app_context():
        form = RegistrationForm(
            formdata=None,
            data={
                "username": "validuser",
                "email": "invalid-email",
                "password": "StrongPassword123",
                "password2": "StrongPassword123",
                "agree_terms": True,
            },
        )
        assert not form.validate()
        assert "email" in form.errors


def test_passwords_do_not_match(app):
    """Test that non-matching passwords fail validation."""
    with app.app_context():
        form = RegistrationForm(
            formdata=None,
            data={
                "username": "validuser",
                "email": "user@example.com",
                "password": "StrongPassword123",
                "password2": "DifferentPassword123",
                "agree_terms": True,
            },
        )
        assert not form.validate()
        assert "password2" in form.errors


def test_agree_terms_required(app):
    """Test that not agreeing to terms fails validation."""
    with app.app_context():
        form = RegistrationForm(
            formdata=None,
            data={
                "username": "validuser",
                "email": "user@example.com",
                "password": "StrongPassword123",
                "password2": "StrongPassword123",
                "agree_terms": False,  # User didn't agree to terms
            },
        )
        assert not form.validate()
        assert "agree_terms" in form.errors
