import pytest

from tests.e2e.conftest import E2E_PASSWORD, login


@pytest.mark.e2e
def test_insights_page_loads_for_pro_user(page, e2e_pro_user):
    login(page, e2e_pro_user.username, E2E_PASSWORD)
    page.goto(f"/{e2e_pro_user.username}/insights")
    assert page.title() != ""
    assert "Collection Insights" in page.inner_text("h1")


@pytest.mark.e2e
def test_insights_navbar_dropdown_opens(page, e2e_pro_user):
    """Regression: insights page must load Bootstrap JS so the navbar dropdown works."""
    login(page, e2e_pro_user.username, E2E_PASSWORD)
    page.goto(f"/{e2e_pro_user.username}/insights")
    page.click("#navbarDropdownUser")
    page.wait_for_selector(".dropdown-menu.show", timeout=2000)
    assert page.is_visible(".dropdown-menu.show")


@pytest.mark.e2e
def test_insights_navbar_link_visible_for_pro_user(page, e2e_pro_user):
    login(page, e2e_pro_user.username, E2E_PASSWORD)
    page.goto(f"/{e2e_pro_user.username}/insights")
    page.click("#navbarDropdownUser")
    page.wait_for_selector(".dropdown-menu.show", timeout=2000)
    assert page.is_visible("text=Collection Insights")


@pytest.mark.e2e
def test_insights_redirects_free_user_to_upgrade(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/insights")
    assert "/upgrade" in page.url
