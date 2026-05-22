import pytest

from tests.e2e.conftest import E2E_PASSWORD
from tests.e2e.pages.login import LoginPage


@pytest.mark.e2e
def test_login_success(page, e2e_user_01):
    lp = LoginPage(page)
    lp.login(e2e_user_01.username, E2E_PASSWORD)
    assert lp.is_logged_in()


@pytest.mark.e2e
def test_login_wrong_password(page, e2e_user_01):
    lp = LoginPage(page)
    lp.login(e2e_user_01.username, "wrongpassword")
    assert not lp.is_logged_in()
    assert "not recognized" in lp.error_message()


@pytest.mark.e2e
def test_login_wrong_username(page):
    lp = LoginPage(page)
    lp.login("no_such_user", E2E_PASSWORD)
    assert not lp.is_logged_in()
    assert "not recognized" in lp.error_message()


@pytest.mark.e2e
def test_logout(page, e2e_user_01):
    lp = LoginPage(page)
    lp.login(e2e_user_01.username, E2E_PASSWORD)
    assert lp.is_logged_in()

    page.click("#navbarDropdownUser")
    page.click("a[href='/logout']")
    assert not lp.is_logged_in()


@pytest.mark.e2e
def test_protected_page_redirects_to_login(page):
    page.goto("/bottle/add")
    assert page.url.endswith("/login") or "/login" in page.url
