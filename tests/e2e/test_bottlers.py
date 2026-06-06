import pytest

from tests.e2e.conftest import E2E_PASSWORD, login


@pytest.mark.e2e
def test_add_bottler(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto("/bottler/add")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "Playwright Test Bottler")
    page.fill("input[name=region_1]", "Vergennes")
    page.fill("input[name=region_2]", "VT")
    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Playwright Test Bottler" in page.content()


@pytest.mark.e2e
def test_edit_bottler(page, e2e_user_01, bottler_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    b = bottler_for_user_01
    page.goto(f"/{e2e_user_01.username}/bottler/{b.user_num}/edit")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "")
    page.fill("input[name=name]", "Edited Bottler Name")
    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Edited Bottler Name" in page.content()


@pytest.mark.e2e
def test_delete_bottler(page, e2e_user_01, bottler_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    b = bottler_for_user_01
    name = b.name
    page.goto(f"/{e2e_user_01.username}/bottler/{b.user_num}/delete")
    page.wait_for_load_state("networkidle")

    # Flash message may contain the name as plain text; assert no link to the deleted bottler
    assert page.locator(f"a:has-text('{name}')").count() == 0
