"""
Regression tests for the ABV/Proof column on detail pages.

Covers the bug from #375 where Alpine.store('abvDisplay') was only
initialized on the bottle list page, leaving the column empty on
distillery, bottler, and barrel-picker detail pages.
"""

import re

import pytest

from tests.e2e.conftest import E2E_PASSWORD, login

ABV = 65.0
EXPECTED_ABV = "65.00%"
EXPECTED_PROOF = "130.00°"


@pytest.mark.e2e
def test_distillery_detail_abv_column_populated(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    d = distillery_with_abv_bottle
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}")
    page.wait_for_load_state("networkidle")

    abv_span = page.locator("span", has_text=re.compile(r"65\.00%")).first
    assert abv_span.is_visible(), "ABV value should be visible by default on distillery detail page"


@pytest.mark.e2e
def test_distillery_detail_proof_toggle(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    d = distillery_with_abv_bottle
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}")
    page.wait_for_load_state("networkidle")

    assert page.locator("span", has_text=re.compile(r"65\.00%")).first.is_visible()

    page.select_option("select:has(option[value='proof'])", "proof")
    page.wait_for_timeout(300)

    assert page.locator("span", has_text=re.compile(r"130\.00°")).first.is_visible(), (
        "Proof value should be visible after toggling to Proof"
    )
    assert not page.locator("span", has_text=re.compile(r"65\.00%")).first.is_visible(), (
        "ABV value should be hidden after toggling to Proof"
    )


@pytest.mark.e2e
def test_abv_proof_preference_persists_across_navigation(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    d = distillery_with_abv_bottle
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}")
    page.wait_for_load_state("networkidle")

    page.select_option("select:has(option[value='proof'])", "proof")
    page.wait_for_timeout(300)

    # Navigate away and back
    page.goto("/")
    page.wait_for_load_state("networkidle")
    page.goto(f"/{e2e_user_01.username}/distillery/{d.user_num}")
    page.wait_for_load_state("networkidle")

    assert page.locator("span", has_text=re.compile(r"130\.00°")).first.is_visible(), (
        "Proof preference should persist across page navigation via cookie"
    )
