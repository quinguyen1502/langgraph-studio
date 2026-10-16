"""Engine/session factory and schema migration (Alembic) bootstrap."""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from ..core import config

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def make_engine(url: str | None = None) -> Engine:
    url = config.normalise_db_url(url or config.DATABASE_URL)
    sqlite = url.startswith("sqlite")
    eng = create_engine(url, future=True, connect_args={"check_same_thread": False, "timeout": 15} if sqlite else {"connect_timeout": 10},
                        pool_pre_ping=not sqlite)
    if sqlite:
        @event.listens_for(eng, "connect")
        def _pragmas(dbapi_conn, _):  # same behaviour as the MVP: WAL + 15 s busy timeout
            cur = dbapi_conn.cursor(); cur.execute("PRAGMA journal_mode=WAL"); cur.close()
    return eng


class Database:
    """Owns the engine and hands out sessions; one instance per app (see api.deps)."""
    def __init__(self, url: str | None = None):
        self.url = config.normalise_db_url(url or config.DATABASE_URL)
        self.engine = make_engine(self.url)
        self._factory = sessionmaker(self.engine, expire_on_commit=False)

    def session(self) -> Session:
        return self._factory()

    def migrate(self) -> None:
        """Upgrade to the latest Alembic revision (idempotent; adopts pre-Alembic SQLite files)."""
        from alembic import command
        from alembic.config import Config
        cfg = Config()
        cfg.set_main_option("script_location", os.path.normpath(MIGRATIONS_DIR))
        cfg.set_main_option("sqlalchemy.url", self.url.replace("%", "%%"))
        with self.engine.begin() as conn:
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
