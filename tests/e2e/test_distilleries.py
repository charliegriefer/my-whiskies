import pytest

from tests.e2e.conftest import E2E_PASSWORD, login


@pytest.mark.e2e
def test_add_distillery(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto("/distillery_add")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "Playwright Test Distillery")
    page.fill("input[name=region_1]", "Austin")
    page.fill("input[name=region_2]", "TX")
    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Playwright Test Distillery" in page.content()


@pytest.mark.e2e
def test_edit_distillery(page, e2e_user_01, distillery_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    d = distillery_for_user_01
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}/edit")
    page.wait_for_load_state("networkidle")

    page.fill("input[name=name]", "")
    page.fill("input[name=name]", "Edited Distillery Name")
    page.click("[type=submit]")
    page.wait_for_load_state("networkidle")

    assert "Edited Distillery Name" in page.content()


@pytest.mark.e2e
def test_delete_distillery(page, e2e_user_01, distillery_for_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    d = distillery_for_user_01
    name = d.name
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}/delete")
    page.wait_for_load_state("networkidle")

    # Flash message may contain the name as plain text; assert no link to the deleted distillery
    assert page.locator(f"a:has-text('{name}')").count() == 0
