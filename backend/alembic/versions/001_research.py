"""Initial evidence and research schema.

Revision ID: 001_research
Revises:
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_research"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("fb_investigations", sa.Column("id", sa.Text(), primary_key=True),
                    sa.Column("payload", JSONB(), nullable=False))
    op.create_table("fb_sources", sa.Column("id", sa.Text(), primary_key=True),
                    sa.Column("investigation_id", sa.Text(), sa.ForeignKey("fb_investigations.id"), nullable=False),
                    sa.Column("sha256", sa.String(64), nullable=False),
                    sa.Column("storage_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
                    sa.Column("payload", JSONB(), nullable=False),
                    sa.UniqueConstraint("investigation_id", "sha256"))
    op.create_table("fb_citations", sa.Column("id", sa.Text(), primary_key=True),
                    sa.Column("source_id", sa.Text(), sa.ForeignKey("fb_sources.id"), nullable=False),
                    sa.Column("payload", JSONB(), nullable=False))
    op.create_table("fb_experiments", sa.Column("id", sa.Text(), primary_key=True),
                    sa.Column("investigation_id", sa.Text(), sa.ForeignKey("fb_investigations.id"), nullable=False),
                    sa.Column("source_id", sa.Text(), sa.ForeignKey("fb_sources.id"), nullable=False),
                    sa.Column("citation_id", sa.Text(), sa.ForeignKey("fb_citations.id"), nullable=False),
                    sa.Column("fuel", sa.Text(), nullable=False),
                    sa.Column("payload", JSONB(), nullable=False))
    op.create_table("fb_charts", sa.Column("id", sa.Text(), primary_key=True),
                    sa.Column("investigation_id", sa.Text(), sa.ForeignKey("fb_investigations.id"), nullable=False),
                    sa.Column("source_id", sa.Text(), sa.ForeignKey("fb_sources.id"), nullable=False),
                    sa.Column("payload", JSONB(), nullable=False))
    for table in ["fb_sources", "fb_experiments", "fb_charts"]:
        op.create_index(f"ix_{table}_investigation", table, ["investigation_id"])
    op.create_index("ix_fb_citations_source", "fb_citations", ["source_id"])
    op.create_index("ix_fb_experiments_fuel", "fb_experiments", ["fuel"])
    # API uses the server connection. No direct public PostgREST access by default.
    for table in ["fb_investigations", "fb_sources", "fb_citations", "fb_experiments", "fb_charts"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"REVOKE ALL ON TABLE {table} FROM PUBLIC")
        for role in ["anon", "authenticated"]:
            op.execute(f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{role}') "
                       f"THEN REVOKE ALL ON TABLE {table} FROM {role}; END IF; END $$")


def downgrade():
    for table in ["fb_charts", "fb_experiments", "fb_citations", "fb_sources", "fb_investigations"]:
        op.drop_table(table)
