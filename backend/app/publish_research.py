"""Load a validated slice; remote writes require explicit --upload."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.database import engine
from app.ingestion import digest


async def publish(bundle: dict, root: Path, upload: bool):
    if not upload and make_url(settings.database_url).host not in {"localhost", "127.0.0.1", "db"}:
        raise ValueError("Local mode refuses a remote database")
    sources = {s["id"]: s for s in bundle["sources"]}
    citations = {c["id"]: c for c in bundle["citations"]}
    for citation in citations.values():
        if citation["source_id"] not in sources:
            raise ValueError("Orphan citation")
    for chart in bundle["charts"]:
        for point in chart["points"]:
            if citations[point["citation_id"]]["source_id"] != chart["source_id"]:
                raise ValueError("Chart citation mismatch")
    for experiment in bundle["experiments"]:
        if citations[experiment["citation_id"]]["source_id"] != experiment["source_id"]:
            raise ValueError("Experiment citation mismatch")
    root = root.resolve()
    for source in sources.values():
        path = (root / source["relative_paths"][0]).resolve()
        if root not in path.parents or digest(path) != source["sha256"]:
            raise ValueError("Source path/checksum mismatch")
    if upload:
        if not settings.supabase_url or not settings.supabase_secret_key:
            raise ValueError("Supabase configuration missing")
        async with httpx.AsyncClient(timeout=60) as client:
            for source in sources.values():
                path = root / source["relative_paths"][0]
                from urllib.parse import quote
                url = (settings.supabase_url.rstrip("/") + "/storage/v1/object/"
                       + quote(settings.supabase_storage_bucket, safe="") + "/"
                       + quote(source["storage_key"], safe="/"))
                headers = {"apikey": settings.supabase_secret_key,
                           "Authorization": f"Bearer {settings.supabase_secret_key}"}
                response = await client.post(url, headers={**headers, "Content-Type": source["media_type"]},
                                             content=path.read_bytes())
                if response.status_code not in (200, 201, 400, 409):
                    raise RuntimeError(f"Upload failed: HTTP {response.status_code}")
                # Verify bytes even for an existing content-addressed object; never overwrite it.
                response = await client.get(url.replace("/object/", "/object/authenticated/", 1), headers=headers)
                if response.status_code != 200:
                    raise RuntimeError("Uploaded source could not be verified")
                import hashlib
                if hashlib.sha256(response.content).hexdigest() != source["sha256"]:
                    raise ValueError("Stored source checksum mismatch")
    async with engine.begin() as connection:
        for table, rows, columns in [
            ("fb_investigations", bundle["investigations"], []),
            ("fb_sources", bundle["sources"], ["investigation_id", "sha256"]),
            ("fb_citations", bundle["citations"], ["source_id"]),
            ("fb_experiments", bundle["experiments"], ["investigation_id", "source_id", "citation_id", "fuel"]),
            ("fb_charts", bundle["charts"], ["investigation_id", "source_id"]),
        ]:
            batch = []
            for row in rows:
                fields = ["id", *columns, "payload"]
                params = {key: row[key] for key in ["id", *columns]}
                params["payload"] = json.dumps(row, allow_nan=False)
                if table == "fb_sources":
                    fields.append("storage_verified")
                    params["storage_verified"] = upload
                values = ["CAST(:payload AS jsonb)" if f == "payload" else f":{f}" for f in fields]
                updates = [f"{f}=EXCLUDED.{f}" for f in fields if f != "id"]
                batch.append(params)
            if batch:
                await connection.execute(text(
                    f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(values)}) "
                    f"ON CONFLICT (id) DO UPDATE SET {','.join(updates)}"), batch)
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--upload", action="store_true", help="Upload verified assets and write configured remote DB")
    args = parser.parse_args()
    asyncio.run(publish(json.loads(args.bundle.read_text()), args.input, args.upload))
    print("Research slice loaded; remote assets verified." if args.upload else "Local research slice loaded.")


if __name__ == "__main__":
    main()
