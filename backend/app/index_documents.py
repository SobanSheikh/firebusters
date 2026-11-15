"""Embed published PDF pages. Resumable; remote writes require --remote."""

import argparse
import asyncio

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.database import engine
from app.embeddings import MODEL, embed, vector_literal
from app.ingestion import chunks_for, stable_id


def page_chunks(page: dict):
    # Small passages limit gte-small's 512-token truncation risk for scientific text.
    for chunk in chunks_for(page, size=400, overlap=80):
        chunk["id"] = stable_id("embedding", MODEL, chunk["id"], chunk["text"])
        yield chunk


async def index(remote: bool):
    if not remote and make_url(settings.database_url).host not in {"localhost", "127.0.0.1", "db"}:
        raise ValueError("Remote database requires --remote")
    async with engine.connect() as connection:
        pages = (await connection.execute(text(
            "SELECT c.payload FROM fb_citations c JOIN fb_sources s ON s.id=c.source_id "
            "WHERE c.payload->'locator'->>'kind'='pdf_page' "
            "AND (:local OR s.storage_verified) ORDER BY c.id"), {"local": not remote})).scalars().all()
        existing = set((await connection.execute(text(
            "SELECT id FROM fb_chunks WHERE model=:model"), {"model": MODEL})).scalars())
    pending = [c for page in pages for c in page_chunks(page) if c["id"] not in existing]
    print(f"PDF pages: {len(pages)}; pending chunks: {len(pending)}", flush=True)
    for start in range(0, len(pending), 12):
        batch = pending[start:start + 12]
        groups = await asyncio.gather(*[
            embed([c["text"] for c in batch[offset:offset + 4]])
            for offset in range(0, len(batch), 4)
        ])
        vectors = [vector for group in groups for vector in group]
        async with engine.begin() as connection:
            # Both installations resolve the vector operator/type with this search path.
            await connection.execute(text("SET LOCAL search_path TO public, extensions"))
            await connection.execute(text(
                "INSERT INTO fb_chunks (id,citation_id,model,text,start_char,end_char,embedding) "
                "VALUES (:id,:citation_id,:model,:text,:start_char,:end_char,:embedding) "
                "ON CONFLICT (id) DO NOTHING"), [
                    {**c, "model": MODEL, "embedding": vector_literal(v)}
                    for c, v in zip(batch, vectors, strict=True)])
        print(f"Indexed {min(start + 12, len(pending))}/{len(pending)}", flush=True)
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(index(args.remote))
    except Exception as error:
        # Avoid printing connection strings/headers in operational output.
        raise SystemExit(f"Indexing stopped ({type(error).__name__}); completed batches are reusable.") from None
