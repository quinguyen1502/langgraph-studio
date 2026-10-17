"""TASK-0030: optional extra HTTP headers on a credential (OpenRouter HTTP-Referer / X-Title), JSON text."""
from alembic import op
import sqlalchemy as sa

revision = "0023_credential_headers"
down_revision = "0022_teams_audit"


def upgrade():
    cols = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("credentials")}
    if "headers" not in cols:
        op.add_column("credentials", sa.Column("headers", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("credentials", "headers")
