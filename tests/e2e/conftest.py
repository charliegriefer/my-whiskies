import os
import sqlite3
import threading
from datetime import datetime

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.serving import make_server

from config import TestConfig
from mywhiskies.app import create_app
from mywhiskies.database import init_db
from mywhiskies.extensions import db
from mywhiskies.models import BarrelPicker, Bottle, Bottler, Distillery, User, UserLogin

E2E_PASSWORD = "E2eTestPass1"


class E2EConfig(TestConfig):
    # File-based SQLite so the live server thread can see committed data
    SQLALCHEMY_DATABASE_URI = "sqlite:///e2e_test.db"
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}


# Enable WAL mode on every SQLite connection so the live server thread and the
# test thread can write concurrently without blocking each other.
@event.listens_for(Engine, "connect")
def set_sqlite_wal_mode(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


# ── Override parent conftest autouse fixtures ────────────────────────────────
# E2E tests commit real data so the live server can read it; we don't want
# per-test transaction rollbacks or Flask-Login's logout_user() called outside
# a request context.


@pytest.fixture(scope="function", autouse=True)
def session(app):
    yield


@pytest.fixture(autouse=True)
def logged_out_user():
    yield


# ── App + live server ────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def app():
    app = create_app(config_class=E2EConfig)
    with app.app_context():
        init_db()
        yield app
        db.session.remove()
        db.drop_all()
    db_path = os.path.join(os.getcwd(), "e2e_test.db")
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="session")
def _server_url(app):
    # Named to avoid conflicting with pytest-flask's live_server fixture detection
    server = make_server("127.0.0.1", 0, app)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(scope="session")
def base_url(_server_url):
    return _server_url


# ── Helpers ──────────────────────────────────────────────────────────────────


def _delete_user_and_owned_data(user):
    """Delete a user and all their owned rows, avoiding NOT NULL FK violations."""
    for bottle in db.session.query(Bottle).filter_by(user_id=user.id).all():
        bottle.distilleries = []
        bottle.barrel_pickers = []
    db.session.flush()
    db.session.query(Bottle).filter_by(user_id=user.id).delete()
    db.session.query(Bottler).filter_by(user_id=user.id).delete()
    db.session.query(Distillery).filter_by(user_id=user.id).delete()
    db.session.query(BarrelPicker).filter_by(user_id=user.id).delete()
    db.session.query(UserLogin).filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()


# ── Test users (created once for the whole session) ──────────────────────────


@pytest.fixture(scope="session")
def e2e_user_01(app):
    user = User(
        username="e2e_user_01",
        email="e2e_user_01@example.com",
        email_confirmed=True,
        email_confirm_date=datetime(2024, 1, 1),
    )
    user.set_password(E2E_PASSWORD)
    db.session.add(user)
    db.session.commit()
    yield user
    _delete_user_and_owned_data(user)


@pytest.fixture(scope="session")
def e2e_user_02(app):
    user = User(
        username="e2e_user_02",
        email="e2e_user_02@example.com",
        email_confirmed=True,
        email_confirm_date=datetime(2024, 1, 1),
    )
    user.set_password(E2E_PASSWORD)
    db.session.add(user)
    db.session.commit()
    yield user
    _delete_user_and_owned_data(user)


@pytest.fixture(scope="session")
def e2e_pro_user(app):
    user = User(
        username="e2e_pro_user",
        email="e2e_pro_user@example.com",
        email_confirmed=True,
        email_confirm_date=datetime(2024, 1, 1),
        is_pro=True,
    )
    user.set_password(E2E_PASSWORD)
    db.session.add(user)
    db.session.commit()
    yield user
    _delete_user_and_owned_data(user)


# ── Per-test data fixtures ────────────────────────────────────────────────────


@pytest.fixture
def distillery_for_user_02(app, e2e_user_02):
    """A distillery owned by user_02 — used to verify user_01 can't edit it."""
    distillery = Distillery(
        name="E2E Test Distillery",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_02.id,
    )
    db.session.add(distillery)
    db.session.commit()
    yield distillery
    db.session.delete(distillery)
    db.session.commit()


@pytest.fixture
def bottler_for_user_02(app, e2e_user_02):
    """A bottler owned by user_02 — used to verify user_01 can't edit it."""
    bottler = Bottler(
        name="E2E Test Bottler",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_02.id,
    )
    db.session.add(bottler)
    db.session.commit()
    yield bottler
    db.session.delete(bottler)
    db.session.commit()


@pytest.fixture(scope="session")
def distillery_with_abv_bottle(app, e2e_user_01):
    """A distillery + bottle with known ABV for ABV/Proof toggle regression tests."""
    distillery = Distillery(
        name="E2E ABV Test Distillery",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_01.id,
    )
    db.session.add(distillery)
    db.session.commit()

    bottle = Bottle(
        name="E2E ABV Test Bottle",
        type="BOURBON",
        abv=65.0,
        user_id=e2e_user_01.id,
    )
    bottle.distilleries = [distillery]
    db.session.add(bottle)
    db.session.commit()

    yield distillery

    bottle.distilleries = []
    db.session.commit()
    db.session.delete(bottle)
    db.session.delete(distillery)
    db.session.commit()


@pytest.fixture
def distillery_for_user_01(app, e2e_user_01):
    """A distillery owned by user_01 for CRUD tests."""
    distillery = Distillery(
        name="E2E User01 Test Distillery",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_01.id,
    )
    db.session.add(distillery)
    db.session.commit()
    yield distillery
    db.session.expire_all()
    try:
        d = db.session.get(Distillery, distillery.id)
        if d:
            db.session.delete(d)
            db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def bottler_for_user_01(app, e2e_user_01):
    """A bottler owned by user_01 for CRUD tests."""
    bottler = Bottler(
        name="E2E User01 Test Bottler",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_01.id,
    )
    db.session.add(bottler)
    db.session.commit()
    yield bottler
    db.session.expire_all()
    try:
        b = db.session.get(Bottler, bottler.id)
        if b:
            db.session.delete(b)
            db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def bottle_for_user_01(app, e2e_user_01):
    """A bottle owned by user_01 for CRUD tests (includes its own distillery)."""
    distillery = Distillery(
        name="E2E Bottle Test Distillery",
        region_1="Testville",
        region_2="TX",
        user_id=e2e_user_01.id,
    )
    db.session.add(distillery)
    db.session.commit()

    bottle = Bottle(
        name="E2E User01 Test Bottle",
        type="BOURBON",
        user_id=e2e_user_01.id,
    )
    bottle.distilleries = [distillery]
    db.session.add(bottle)
    db.session.commit()

    yield bottle, distillery

    db.session.expire_all()
    try:
        bt = db.session.get(Bottle, bottle.id)
        if bt:
            bt.distilleries = []
            db.session.commit()
            db.session.delete(bt)
            db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        d = db.session.get(Distillery, distillery.id)
        if d:
            db.session.delete(d)
            db.session.commit()
    except Exception:
        db.session.rollback()


@pytest.fixture
def bottle_for_user_02(app, e2e_user_02, distillery_for_user_02):
    """A bottle owned by user_02 — used to verify user_01 can't edit/delete it."""
    bottle = Bottle(
        name="E2E Test Bottle",
        type="BOURBON",
        user_id=e2e_user_02.id,
    )
    bottle.distilleries = [distillery_for_user_02]
    db.session.add(bottle)
    db.session.commit()
    yield bottle
    db.session.delete(bottle)
    db.session.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────


def login(page, username, password):
    """Fill and submit the login form, then wait until the session is confirmed."""
    page.goto("/login")
    page.fill("input[name=username]", username)
    page.fill("input[name=password]", password)
    page.click("input[type=submit][name=submit]")
    page.wait_for_selector("#navbarDropdownUser")
