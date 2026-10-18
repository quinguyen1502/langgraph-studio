"""Alembic migrations on a fresh Postgres database (TASK-0009).

Runs when TEST_DATABASE_URL (or DATABASE_URL) points at Postgres; the role needs CREATEDB.
A throwaway database is created and dropped, so the configured one is never touched."""
import os, uuid
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from app.core.config import normalise_db_url
from app.models.database import Database
from app.services.seed import bootstrap
from app.models.database import head_revision

HEAD = head_revision()

URL = normalise_db_url(os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="set TEST_DATABASE_URL=postgresql://... to run")


@pytest.fixture
def fresh_pg():
    name = f"lgs_test_{uuid.uuid4().hex[:8]}"
    admin = create_engine(make_url(URL).set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as c: c.execute(text(f'CREATE DATABASE "{name}"'))
    db = Database(make_url(URL).set(database=name).render_as_string(hide_password=False))
    try: yield db
    finally:
        db.engine.dispose()
        with admin.connect() as c: c.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        admin.dispose()


def test_migrations_and_seed_on_fresh_postgres(fresh_pg):
    bootstrap(fresh_pg); bootstrap(fresh_pg)  # second run is a no-op (idempotent upgrade + seed)
    insp = inspect(fresh_pg.engine)
    assert fresh_pg.engine.dialect.name == "postgresql"
    assert {"users", "workflows", "runs", "credentials", "alembic_version"} <= set(insp.get_table_names())
    with fresh_pg.engine.connect() as c:
        assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == HEAD
        assert c.execute(text("SELECT count(*) FROM users WHERE email='admin@example.com'")).scalar_one() == 1
        assert c.execute(text("SELECT count(*) FROM workflows")).scalar_one() >= 1
