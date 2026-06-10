from flask import url_for
from flask.testing import FlaskClient

from mywhiskies.models import User


def test_insights_requires_login(client: FlaskClient, test_user_01: User) -> None:
    response = client.get(url_for("user.insights", username=test_user_01.username))
    assert response.status_code == 302
    assert url_for("auth.login") in response.headers["Location"]


def test_insights_redirects_free_user_to_upgrade(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    assert not test_user_01.is_pro
    response = logged_in_user_01.get(
        url_for("user.insights", username=test_user_01.username),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Upgrade" in response.data
    assert b"Pro" in response.data


def test_insights_forbidden_for_other_user(logged_in_user_01: FlaskClient, test_user_02: User) -> None:
    response = logged_in_user_01.get(url_for("user.insights", username=test_user_02.username))
    assert response.status_code == 403


def test_insights_renders_for_pro_user(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    test_user_01.is_pro = True
    response = logged_in_user_01.get(url_for("user.insights", username=test_user_01.username))
    assert response.status_code == 200
    assert b"Collection Insights" in response.data
    assert b"chart.js" in response.data.lower()


def test_insights_shows_correct_bottle_count(logged_in_user_01: FlaskClient, test_user_01: User) -> None:
    test_user_01.is_pro = True
    response = logged_in_user_01.get(url_for("user.insights", username=test_user_01.username))
    assert str(len(test_user_01.bottles)).encode() in response.data
