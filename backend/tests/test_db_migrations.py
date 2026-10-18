from app.models import Run
"""Alembic: fresh DB gets the schema; a pre-Alembic (raw-SQL era) SQLite file is adopted without data loss."""
import sqlite3
from sqlalchemy import inspect
from app.models.database import Database
from app.repositories import WorkflowRepository
from app.services.seed import bootstrap


def test_fresh_database(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'fresh.db'}"); bootstrap(db)
    insp = inspect(db.engine)
    assert {"users", "workflows", "runs", "credentials", "alembic_version"} <= set(insp.get_table_names())
    cols = [c["name"] for c in insp.get_columns("runs")]
    assert cols[:8] == ["id", "workflow_id", "input", "events", "final_state", "status", "started", "ended"]  # MVP order kept
    assert set(cols) == set(Run.__table__.columns.keys())  # migrations match the ORM model
    assert WorkflowRepository(db).exists("example")
    bootstrap(db)  # idempotent


def test_legacy_database_is_adopted(tmp_path):
    p = tmp_path / "legacy.db"; c = sqlite3.connect(p)
    c.execute("CREATE TABLE users(id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, created REAL)")
    c.execute("CREATE TABLE workflows(id TEXT PRIMARY KEY, name TEXT, data TEXT, updated REAL)")  # pre-owner schema
    c.execute("CREATE TABLE runs(id TEXT PRIMARY KEY, workflow_id TEXT, input TEXT, events TEXT, final_state TEXT, status TEXT, started REAL, ended REAL)")
    c.execute("INSERT INTO workflows VALUES('old','Old','{\"name\":\"Old\"}',1.0)"); c.commit(); c.close()
    db = Database(f"sqlite:///{p}"); bootstrap(db)
    w = WorkflowRepository(db).get("old")
    assert w.name == "Old" and w.owner == "admin"
    assert db.engine.dialect.name == "sqlite"
    with db.engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"


def test_pr2_era_database_with_credentials_table_is_adopted(tmp_path):
    p = tmp_path / "pr2.db"; c = sqlite3.connect(p)
    c.execute("CREATE TABLE credentials(id TEXT PRIMARY KEY, owner TEXT, name TEXT, provider TEXT, base_url TEXT, secret TEXT, hint TEXT, created REAL)")
    c.execute("INSERT INTO credentials VALUES('c1','admin','k','openai',NULL,'tok','••••abcd',1.0)"); c.commit(); c.close()
    db = Database(f"sqlite:///{p}"); bootstrap(db)
    from app.repositories import CredentialRepository
    assert CredentialRepository(db).get_owned("c1", "admin").hint == "••••abcd"
