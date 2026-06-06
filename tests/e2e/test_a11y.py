"""
Accessibility audit using axe-core.
Each test navigates to a page, injects axe-core, runs the analysis,
and asserts zero violations.
"""

from pathlib import Path

import pytest

from tests.e2e.conftest import E2E_PASSWORD, login

_AXE_JS = (Path(__file__).parent / "axe.min.js").read_text()


def _check_a11y(page):
    """Inject axe-core, run analysis, return list of violation dicts."""
    page.evaluate(_AXE_JS)
    violations = page.evaluate("async () => { const r = await axe.run(); return r.violations; }")
    return violations


def _fmt(violations):
    lines = []
    for v in violations:
        lines.append(f"\n[{v['impact']}] {v['id']}: {v['description']}")
        for node in v.get("nodes", [])[:2]:
            lines.append(f"  → {node.get('html', '')[:120]}")
    return "".join(lines)


# ── Anonymous pages ───────────────────────────────────────────────────────────


@pytest.mark.e2e
def test_a11y_login_page(page):
    page.goto("/login")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_register_page(page):
    page.goto("/register")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


# ── Authenticated pages ───────────────────────────────────────────────────────


@pytest.mark.e2e
def test_a11y_home(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_bottle_list(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/bottles")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_bottle_detail(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/bottles")
    page.wait_for_load_state("networkidle")
    # Click the first bottle link
    page.locator("table tbody tr td a").first.click()
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_bottle_add_form(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto("/bottle/add")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_distillery_list(page, e2e_user_01, distillery_with_abv_bottle):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/distilleries")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_bottler_list(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/bottlers")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_barrel_picker_list(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto(f"/{e2e_user_01.username}/barrel-pickers")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)


@pytest.mark.e2e
def test_a11y_account_page(page, e2e_user_01):
    login(page, e2e_user_01.username, E2E_PASSWORD)
    page.goto("/account")
    page.wait_for_load_state("networkidle")
    violations = _check_a11y(page)
    assert violations == [], _fmt(violations)
