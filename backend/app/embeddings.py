"""Supabase gte-small client; no local model or provider-specific LLM dependency."""

import json
import math

import httpx

from app.core.config import settings

MODEL = "gte-small/mean-normalized-v1"
DIMENSIONS = 384


def validate_vectors(payload: dict, count: int) -> list[list[float]]:
    vectors = payload.get("embeddings")
    if payload.get("model") != MODEL or not isinstance(vectors, list) or len(vectors) != count:
        raise ValueError("Embedding model or count mismatch")
    for vector in vectors:
        if (not isinstance(vector, list) or len(vector) != DIMENSIONS
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector)
                or not 0.98 <= sum(v * v for v in vector) <= 1.02):
            raise ValueError("Invalid normalized embedding")
    return vectors


async def embed(texts: list[str]) -> list[list[float]]:
    if not settings.supabase_url or not settings.embedding_secret:
        raise ValueError("Supabase embedding function is not configured")
    if not 1 <= len(texts) <= 4 or any(not t.strip() or len(t) > 1500 for t in texts):
        raise ValueError("Embedding input exceeds bounds")
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.post(
            settings.supabase_url.rstrip("/") + "/functions/v1/" + settings.embedding_function_name,
            headers={"x-embedding-secret": settings.embedding_secret},
            json={"texts": texts})
        response.raise_for_status()
        return validate_vectors(response.json(), len(texts))


def vector_literal(vector: list[float]) -> str:
    return json.dumps(vector, allow_nan=False, separators=(",", ":"))
