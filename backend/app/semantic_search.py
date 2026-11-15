"""Optional semantic retrieval; failures preserve existing keyword evidence."""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import httpx

from app.core.config import settings
from app.core.database import engine
from app.embeddings import MODEL, embed, vector_literal

logger = logging.getLogger(__name__)


async def semantic_evidence(question: str) -> list[dict]:
    if not settings.embedding_secret:
        return []
    try:
        # Avoid paying for query embeddings before any document vectors are present.
        async with engine.connect() as connection:
            ready = await connection.scalar(text(
                "SELECT EXISTS(SELECT 1 FROM fb_chunks WHERE model=:model)"), {"model": MODEL})
        if not ready:
            return []
        vector = (await embed([question]))[0]
        async with engine.begin() as connection:
            await connection.execute(text("SET LOCAL search_path TO public, extensions"))
            rows = (await connection.execute(text(
                "SELECT k.id,k.citation_id,k.text,k.start_char,k.end_char,c.payload,"
                "s.payload->>'filename' AS filename, 1-(k.embedding <=> :vector) AS similarity "
                "FROM fb_chunks k JOIN fb_citations c ON c.id=k.citation_id "
                "JOIN fb_sources s ON s.id=c.source_id WHERE k.model=:model "
                "ORDER BY k.embedding <=> :vector, k.id LIMIT 6"),
                {"vector": vector_literal(vector), "model": MODEL})).mappings().all()
        evidence = []
        for row in rows:
            if any(e["citation_id"] == row["citation_id"] for e in evidence):
                continue
            evidence.append({
                "citation_id": row["citation_id"], "kind": "document_passage",
                "label": f"{row['filename']} — page {row['payload']['locator']['page']}",
                "data": {"text": row["text"], "page": row["payload"]["locator"]["page"],
                         "start_char": row["start_char"], "end_char": row["end_char"],
                         "retrieval": "semantic candidate, not proof of relevance",
                         "extraction": "PDF text; diagrams and tables may be incomplete"}})
            if len(evidence) == 3:
                break
        return evidence
    except (httpx.HTTPError, ValueError, SQLAlchemyError, KeyError, TypeError):
        logger.warning("Semantic retrieval unavailable; using keyword evidence")
        return []
