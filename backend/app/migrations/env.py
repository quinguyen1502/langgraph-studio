"""Alembic environment. Used programmatically by models.database.Database.migrate() and by
`alembic -c backend/alembic.ini upgrade head` from the CLI."""
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core import config as settings
from app.models import Base

cfg = context.config
target_metadata = Base.metadata
url = cfg.get_main_option("sqlalchemy.url") or settings.DATABASE_URL


def run_offline():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_online():
    conn = cfg.attributes.get("connection")
    if conn is not None:
        context.configure(connection=conn, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    eng = engine_from_config({"sqlalchemy.url": url}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with eng.connect() as c:
        context.configure(connection=c, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


run_offline() if context.is_offline_mode() else run_online()
