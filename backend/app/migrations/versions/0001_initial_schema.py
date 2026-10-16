"""Initial schema: users, workflows, runs (matches the MVP raw-SQL schema).

Idempotent so databases created before Alembic (no alembic_version table) are adopted as-is:
tables are only created when missing, and the legacy `workflows.owner` column is added if absent.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind()); tables = set(insp.get_table_names())
    if "users" not in tables:
        op.create_table("users",
            sa.Column("id", sa.Text, primary_key=True), sa.Column("email", sa.Text, unique=True),
            sa.Column("password", sa.Text), sa.Column("created", sa.Float))
    if "workflows" not in tables:
        op.create_table("workflows",
            sa.Column("id", sa.Text, primary_key=True), sa.Column("name", sa.Text), sa.Column("data", sa.Text),
            sa.Column("updated", sa.Float), sa.Column("owner", sa.Text))
    elif "owner" not in {c["name"] for c in insp.get_columns("workflows")}:
        op.add_column("workflows", sa.Column("owner", sa.Text))
    if "runs" not in tables:
        op.create_table("runs",
            sa.Column("id", sa.Text, primary_key=True), sa.Column("workflow_id", sa.Text), sa.Column("input", sa.Text),
            sa.Column("events", sa.Text), sa.Column("final_state", sa.Text), sa.Column("status", sa.Text),
            sa.Column("started", sa.Float), sa.Column("ended", sa.Float))


def downgrade() -> None:
    for t in ("runs", "workflows", "users"):
        op.drop_table(t)
