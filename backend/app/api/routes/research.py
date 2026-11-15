"""Read-only research API; source downloads resolve stable IDs."""

import os
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.ingestion import digest

router = APIRouter()


async def records(query, **params):
    async with engine.connect() as connection:
        result = await connection.execute(text(query), params)
        return result.mappings().all()


@router.get("/overview")
async def overview():
    investigations = await records("SELECT payload FROM fb_investigations ORDER BY id")
    charts = await records("SELECT payload FROM fb_charts ORDER BY id")
    fuels = await records("SELECT DISTINCT fuel FROM fb_experiments ORDER BY fuel")
    count = await records("SELECT count(*) AS total FROM fb_experiments")
    return {"investigations": [r["payload"] for r in investigations],
            "charts": [r["payload"] for r in charts],
            "fuels": [r["fuel"] for r in fuels], "experiment_count": count[0]["total"]}


@router.get("/experiments")
async def experiments(fuel: str | None = None, offset: int = Query(0, ge=0),
                      limit: int = Query(25, ge=1, le=100)):
    where = "WHERE fuel = :fuel" if fuel else ""
    params = {"fuel": fuel} if fuel else {}
    rows = await records(f"SELECT payload FROM fb_experiments {where} ORDER BY payload->>'run', id "
                         "LIMIT :limit OFFSET :offset", **params, limit=limit, offset=offset)
    count = await records(f"SELECT count(*) AS total FROM fb_experiments {where}", **params)
    return {"items": [r["payload"] for r in rows], "total": count[0]["total"]}


@router.get("/citations/{citation_id}")
async def citation(citation_id: str):
    rows = await records("SELECT c.payload, s.payload AS source FROM fb_citations c "
                         "JOIN fb_sources s ON s.id=c.source_id WHERE c.id=:id", id=citation_id)
    if not rows:
        raise HTTPException(404, "Citation not found")
    row = rows[0]
    return {**row["payload"], "filename": row["source"]["filename"],
            "sha256": row["source"]["sha256"],
            "source_url": f"/api/v1/research/sources/{row['payload']['source_id']}"}


@router.get("/sources/{source_id}")
async def source(source_id: str):
    rows = await records("SELECT payload, storage_verified FROM fb_sources WHERE id=:id", id=source_id)
    if not rows:
        raise HTTPException(404, "Source not found")
    payload = rows[0]["payload"]
    if settings.environment == "development":
        root = Path(os.environ.get("NASA_DATA_ROOT", "/app/data/ nasa")).resolve()
        path = (root / payload["relative_paths"][0]).resolve()
        if root in path.parents and path.is_file():
            if digest(path) != payload["sha256"]:
                raise HTTPException(409, "Local source changed since ingestion")
            return FileResponse(path, filename=payload["filename"], media_type=payload["media_type"])
    if not rows[0]["storage_verified"]:
        raise HTTPException(503, "Source upload has not been verified")
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise HTTPException(503, "Source storage is not configured")
    base = settings.supabase_url.rstrip("/")
    key = quote(payload["storage_key"], safe="/")
    bucket = quote(settings.supabase_storage_bucket, safe="")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{base}/storage/v1/object/sign/{bucket}/{key}",
                                         headers={"apikey": settings.supabase_secret_key,
                                                  "Authorization": f"Bearer {settings.supabase_secret_key}"},
                                         json={"expiresIn": 300})
            response.raise_for_status()
            signed = response.json()["signedURL"]
            if not signed.startswith("/object/sign/"):
                raise ValueError("Unexpected signed URL path")
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(502, "Source storage is temporarily unavailable") from None
    return RedirectResponse(f"{base}/storage/v1{signed}")
