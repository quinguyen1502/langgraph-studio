"""Alembic: fresh DB gets the schema; a pre-Alembic (raw-SQL era) SQLite file is adopted without data loss."""
import sqlite3
from sqlalchemy import inspect
from app.models.database import Database
from app.repositories import WorkflowRepository
from app.services.seed import bootstrap


def test_fresh_database(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'fresh.db'}"); bootstrap(db)
    insp = inspect(db.engine)
    assert {"users", "workflows", "runs", "alembic_version"} <= set(insp.get_table_names())
    assert [c["name"] for c in insp.get_columns("runs")] == ["id", "workflow_id", "input", "events", "final_state", "status", "started", "ended"]
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
