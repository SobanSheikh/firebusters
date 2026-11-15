"""Page-linked embeddings; private to the server connection."""

from alembic import op

revision = "002_embeddings"
down_revision = "001_research"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Supabase commonly installs vector in extensions; local Postgres uses public.
    op.execute("SET LOCAL search_path TO public, extensions")
    op.execute("""
        CREATE TABLE public.fb_chunks (
            id text PRIMARY KEY,
            citation_id text NOT NULL REFERENCES public.fb_citations(id),
            model text NOT NULL,
            text text NOT NULL,
            start_char integer NOT NULL CHECK (start_char >= 0),
            end_char integer NOT NULL CHECK (end_char > start_char),
            embedding vector(384) NOT NULL,
            CHECK (char_length(text) = end_char - start_char)
        )
    """)
    op.execute("CREATE INDEX ix_fb_chunks_citation ON public.fb_chunks(citation_id)")
    # Exact vector scan is adequate for this small MVP; add HNSW when corpus grows.
    op.execute("ALTER TABLE public.fb_chunks ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL ON TABLE public.fb_chunks FROM PUBLIC")
    for role in ("anon", "authenticated"):
        op.execute(f"DO $$ BEGIN IF EXISTS (SELECT FROM pg_roles WHERE rolname = '{role}') "
                   f"THEN REVOKE ALL ON TABLE public.fb_chunks FROM {role}; END IF; END $$")


def downgrade():
    op.drop_table("fb_chunks")
