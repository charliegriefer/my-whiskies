# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the app
flask run

# Run all tests
pytest

# Run a single test file
pytest tests/unit/bottle/test_bottle_service.py

# Run with coverage
pytest --cov=mywhiskies

# Database migrations
flask db migrate -m "description"
flask db upgrade
flask db downgrade

# Lint and format (run before committing)
ruff check . --fix
ruff format .
```

## Before Committing

Always run the following before committing or pushing:

1. `ruff check . --fix` — auto-fix lint issues
2. `ruff format .` — format code in place
3. `pytest --cov=mywhiskies tests/` — run full test suite

All three must pass cleanly before pushing to main.

## Task and Issue Workflow

GitHub Issues are the single source of truth for all work — backlog, active, and future milestones:

- Use `gh issue list --milestone v0.2.0` (or v0.3.0, v0.4.0) to see what's in scope for a given release.
- When starting a new feature or fix, confirm there is a corresponding GitHub Issue before beginning work.
- Commit messages should reference the issue number where applicable (e.g. `fix: flash message colors (#130)`).

## Architecture

Flask application using the **Blueprint + Service Layer** pattern:

- **`mywhiskies/blueprints/`** — Route handlers, one blueprint per domain (auth, bottle, bottler, distillery, user, core, errors). Views delegate to services and do minimal logic.
- **`mywhiskies/services/`** — All business logic lives here, organized by domain. Views call service functions rather than implementing logic directly.
- **`mywhiskies/models/`** — SQLAlchemy models: `User`, `Bottle`, `BottleImage`, `Bottler`, `Distillery`, and the `bottle_distillery` many-to-many association table.
- **`mywhiskies/forms/`** — WTForms for input validation (auth, bottle, bottler, distillery).
- **`mywhiskies/templates/`** — Jinja2 templates. `_base.html` is the root layout; `navbar.html` and `footer.html` are shared partials.
- **`mywhiskies/extensions.py`** — All Flask extension instances (db, login_manager, mail, migrate) initialized here and imported elsewhere.
- **`config.py`** — Three config classes: `DevConfig`, `ProdConfig`, `TestConfig`. Selected via the `CONFIG` environment variable.

## Key Domain Concepts

- A **Bottle** has a many-to-many relationship with **Distillery** (a bottle can come from multiple distilleries). Bottler is separate from Distillery.
- **BottleImage** records store S3 image metadata (sequence number). Actual images live in AWS S3 bucket `my-whiskies-pics`.
- Bottles, distilleries, and bottlers are all owned by a **User**.

## Testing

Tests use SQLite in-memory and pytest fixtures from `tests/conftest.py`. Key fixtures: `app`, `test_client`, `test_user_01` (has 4 distilleries, 2 bottlers, 3 bottles), `logged_in_user_01`. TestConfig disables CSRF and reCAPTCHA.

Unit tests are in `tests/unit/`, integration tests (full HTTP request/response) in `tests/integration/`.

## Environment

Requires a `.env` file with database URI, secret key, AWS S3 credentials, mail config, and reCAPTCHA keys. `.flaskenv` sets `FLASK_APP=mywhiskies.app:app`.