"""Mobile viewport tests — catch layout regressions on narrow screens."""

import pytest

from tests.e2e.conftest import E2E_PASSWORD, login

IPHONE_VIEWPORT = {"width": 390, "height": 844}


@pytest.mark.e2e
def test_navbar_hamburger_visible_on_mobile(page, e2e_user_01):
    # Login at default (desktop) viewport so the wait_for_selector on #navbarDropdownUser succeeds,
    # then switch to mobile where the collapse toggler should appear.
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.set_viewport_size(IPHONE_VIEWPORT)
    page.goto("/")
    page.wait_for_load_state("networkidle")

    assert page.locator(".navbar-toggler").is_visible(), (
        "Hamburger menu button should be visible on mobile when authenticated"
    )


@pytest.mark.e2e
def test_navbar_expands_on_mobile(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.set_viewport_size(IPHONE_VIEWPORT)
    page.goto("/")
    page.wait_for_load_state("networkidle")

    page.locator(".navbar-toggler").click()
    page.wait_for_selector(".navbar-collapse.show", state="visible", timeout=3000)
    assert page.locator(".navbar-collapse.show").is_visible()


@pytest.mark.e2e
def test_stats_band_content_visible_on_mobile(page):
    """Stats band numbers should be accessible on mobile (2x2 wrap, not clipped)."""
    page.set_viewport_size(IPHONE_VIEWPORT)
    page.goto("/")
    page.wait_for_load_state("networkidle")

    band = page.locator(".stats-band")
    assert band.is_visible()

    labels = page.locator(".stats-band-stat .sbs-l").all()
    assert len(labels) == 4, f"Expected 4 stat labels, got {len(labels)}"
    for label in labels:
        assert label.is_visible(), f"Stat label '{label.inner_text()}' should be visible on mobile"


@pytest.mark.e2e
def test_hero_content_visible_on_mobile(page):
    page.set_viewport_size(IPHONE_VIEWPORT)
    page.goto("/")
    page.wait_for_load_state("networkidle")

    assert page.locator(".hm-headline").is_visible()
    assert page.locator(".hm-hero-img").is_visible()
