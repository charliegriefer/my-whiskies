import pytest

from tests.e2e.conftest import E2E_PASSWORD, login


@pytest.mark.e2e
def test_add_bottle(page, e2e_user_01, distillery_with_abv_bottle):
    """Add a bottle by filling the form — uses distillery_with_abv_bottle as the distillery."""
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto("/bottle/add")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "Playwright Test Bottle")
    page.select_option("#type", "BOURBON")

    # The distillery field is a custom widget backed by a hidden <select>.
    # Click the search input, type to filter, then click the matching item.
    page.click(".distillery-widget input[type=text]")
    page.fill(".distillery-widget input[type=text]", "E2E ABV")
    page.wait_for_selector(".distillery-dropdown .list-group-item", state="visible")
    page.click(".distillery-dropdown .list-group-item")

    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Playwright Test Bottle" in page.content()


@pytest.mark.e2e
def test_edit_bottle(page, e2e_user_01, bottle_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    bottle, _ = bottle_for_user_01
    page.goto(f"/{e2e_user_01.username}/bottle/{bottle.user_num}/edit")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "")
    page.fill("input[name=name]", "Edited Bottle Name")
    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Edited Bottle Name" in page.content()


@pytest.mark.e2e
def test_delete_bottle(page, e2e_user_01, bottle_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    bottle, _ = bottle_for_user_01
    name = bottle.name
    page.goto(f"/{e2e_user_01.username}/bottle/{bottle.user_num}/delete")
    page.wait_for_load_state("networkidle")

    # Flash message may contain the name as plain text; assert no link to the deleted bottle
    assert page.locator(f"a:has-text('{name}')").count() == 0
