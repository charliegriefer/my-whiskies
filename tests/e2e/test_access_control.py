import pytest

from tests.e2e.conftest import E2E_PASSWORD, login


@pytest.mark.e2e
def test_cannot_edit_other_users_bottle(page, e2e_user_01, bottle_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{bottle_for_user_02.user.username}/bottle/{bottle_for_user_02.user_num}/edit")
    assert "Access Denied" in page.content()


@pytest.mark.e2e
def test_cannot_delete_other_users_bottle(page, e2e_user_01, bottle_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{bottle_for_user_02.user.username}/bottle/{bottle_for_user_02.user_num}/delete")
    assert "Access Denied" in page.content()


@pytest.mark.e2e
def test_cannot_edit_other_users_bottler(page, e2e_user_01, bottler_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{bottler_for_user_02.user.username}/bottler/{bottler_for_user_02.user_num}/edit")
    assert "Access Denied" in page.content()


@pytest.mark.e2e
def test_cannot_delete_other_users_bottler(page, e2e_user_01, bottler_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{bottler_for_user_02.user.username}/bottler/{bottler_for_user_02.user_num}/delete")
    assert "Access Denied" in page.content()


@pytest.mark.e2e
def test_cannot_edit_other_users_distillery(page, e2e_user_01, distillery_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{distillery_for_user_02.user.username}/distillery/{distillery_for_user_02.user_num}/edit")
    assert "Access Denied" in page.content()


@pytest.mark.e2e
def test_cannot_delete_other_users_distillery(page, e2e_user_01, distillery_for_user_02):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{distillery_for_user_02.user.username}/distillery/{distillery_for_user_02.user_num}/delete")
    assert "Access Denied" in page.content()
