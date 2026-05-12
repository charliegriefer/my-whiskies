from datetime import datetime, timedelta
from unittest.mock import patch

from mywhiskies.extensions import db
from mywhiskies.models import User
from mywhiskies.services.user.cleanup import (
    delete_inactive_users,
    get_users_to_delete,
    get_users_to_warn,
    warn_inactive_users,
)


def _make_user(username, email, days_ago_registered=None, days_ago_login=None, warned_days_ago=None, confirmed=True):
    user = User(username=username, email=email, email_confirmed=confirmed)
    user.set_password("testpass")
    if days_ago_registered is not None:
        user.date_registered = datetime.utcnow() - timedelta(days=days_ago_registered)
    if days_ago_login is not None:
        user.last_login_at = datetime.utcnow() - timedelta(days=days_ago_login)
    if warned_days_ago is not None:
        user.warned_at = datetime.utcnow() - timedelta(days=warned_days_ago)
    db.session.add(user)
    db.session.commit()
    return user


class TestGetUsersToWarn:
    def test_includes_user_inactive_by_last_login(self, app):
        user = _make_user("stale_login", "stale@example.com", days_ago_login=200)
        result = get_users_to_warn()
        assert user in result

    def test_excludes_user_who_never_logged_in(self, app):
        user = _make_user("never_logged_in", "never@example.com", days_ago_registered=200)
        result = get_users_to_warn()
        assert user not in result

    def test_excludes_recently_active_user(self, app):
        user = _make_user("active", "active@example.com", days_ago_login=10)
        result = get_users_to_warn()
        assert user not in result

    def test_excludes_already_warned_user(self, app):
        user = _make_user("already_warned", "warned@example.com", days_ago_login=200, warned_days_ago=5)
        result = get_users_to_warn()
        assert user not in result

    def test_excludes_unconfirmed_user(self, app):
        user = _make_user("unconfirmed", "unconfirmed@example.com", days_ago_login=200, confirmed=False)
        result = get_users_to_warn()
        assert user not in result

    def test_excludes_deleted_user(self, app):
        user = _make_user("deleted_user", "deleted@example.com", days_ago_login=200)
        user.is_deleted = True
        db.session.commit()
        result = get_users_to_warn()
        assert user not in result


class TestGetUsersToDelete:
    def test_includes_warned_user_past_grace_period(self, app):
        user = _make_user("past_grace", "past@example.com", days_ago_login=220, warned_days_ago=35)
        result = get_users_to_delete()
        assert user in result

    def test_excludes_warned_user_within_grace_period(self, app):
        user = _make_user("in_grace", "grace@example.com", days_ago_login=200, warned_days_ago=10)
        result = get_users_to_delete()
        assert user not in result

    def test_excludes_unwarned_user(self, app):
        user = _make_user("unwarned", "unwarned@example.com", days_ago_login=200)
        result = get_users_to_delete()
        assert user not in result

    def test_excludes_deleted_user(self, app):
        user = _make_user("del_user", "del@example.com", days_ago_login=220, warned_days_ago=35)
        user.is_deleted = True
        db.session.commit()
        result = get_users_to_delete()
        assert user not in result


class TestWarnInactiveUsers:
    def test_warns_eligible_users_and_sets_warned_at(self, app):
        user = _make_user("to_warn", "to_warn@example.com", days_ago_login=200)
        with patch("mywhiskies.services.user.cleanup.send_inactive_account_warning") as mock_send:
            count = warn_inactive_users()
        mock_send.assert_called_once_with(user, 30)
        assert user.warned_at is not None
        assert count == 1

    def test_rolls_back_on_email_failure(self, app):
        _make_user("fail_warn", "fail_warn@example.com", days_ago_login=200)
        exc = Exception("smtp error")
        with patch("mywhiskies.services.user.cleanup.send_inactive_account_warning", side_effect=exc):
            count = warn_inactive_users()
        assert count == 1  # still counted in the list, just failed


class TestDeleteInactiveUsers:
    def test_deletes_eligible_users(self, app):
        user = _make_user("to_delete", "to_delete@example.com", days_ago_login=220, warned_days_ago=35)
        with patch("mywhiskies.services.user.cleanup.delete_user_account") as mock_delete:
            count = delete_inactive_users()
        mock_delete.assert_called_once_with(user)
        assert count == 1

    def test_rolls_back_on_delete_failure(self, app):
        _make_user("fail_delete", "fail_delete@example.com", days_ago_login=220, warned_days_ago=35)
        with patch("mywhiskies.services.user.cleanup.delete_user_account", side_effect=Exception("db error")):
            count = delete_inactive_users()
        assert count == 0
