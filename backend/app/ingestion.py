"""Offline evidence preparation. No credentials, network calls, or database writes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import mimetypes
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

VERSION = "evidence-v1"


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def stable_id(kind: str, *parts: str) -> str:
    value = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return f"{kind}_{hashlib.sha256(value.encode()).hexdigest()}"


def inventory(root: Path) -> list[dict]:
    """Deduplicate bytes within an investigation; preserve every relative alias."""
    sources: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        match = re.search(r"(?:^|/)PSI[_-](\d+)(?:/|$)", relative, re.I)
        investigation = f"PSI-{match[1]}" if match else None
        checksum = digest(path)
        source_id = stable_id("src", investigation or "reference", checksum)
        if source_id in sources:
            sources[source_id]["relative_paths"].append(relative)
            continue
        sources[source_id] = {
            "id": source_id,
            "investigation_id": investigation,
            "sha256": checksum,
            "relative_paths": [relative],
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "extension": path.suffix.lower(),
            "storage_key": f"sources/{investigation or 'reference'}/{checksum}/original"
            f"{path.suffix.lower()}",
            "canonical_url": None,
            "processing_version": VERSION,
            "status": "catalogued",
            "review_required": True,
        }
    return list(sources.values())


def evidence(source: dict, locator: dict, **payload) -> dict:
    locator_key = json.dumps(locator, sort_keys=True, separators=(",", ":"))
    return {
        "id": stable_id("cite", source["id"], locator_key),
        "source_id": source["id"],
        "locator": locator,
        "processing_version": VERSION,
        **payload,
    }


def csv_records(path: Path, source: dict):
    """Preserve positional cells, duplicate headers, blanks and record locators."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for number, cells in enumerate(reader, start=1):
            yield evidence(
                source,
                {"kind": "csv_record", "record": number},
                cells=cells,
            )


def numeric_profiles(records: list[dict]) -> list[dict]:
    """Descriptive numeric profiles only; do not infer headers, units or physics."""
    width = max((len(record["cells"]) for record in records), default=0)
    profiles = []
    for column in range(width):
        values = []
        nonnumeric = 0
        missing = 0
        for record in records:
            cells = record["cells"]
            cell = cells[column].strip() if column < len(cells) else ""
            if not cell:
                missing += 1
                continue
            try:
                value = float(cell)
            except ValueError:
                nonnumeric += 1
                continue
            if not math.isfinite(value):
                nonnumeric += 1
                continue
            values.append(value)
        profiles.append({
            "column_index": column,
            "finite_numeric_count": len(values),
            "missing_count": missing,
            "other_count": nonnumeric,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "unit": None,
            "review_required": True,
        })
    return profiles


def pdf_pages(path: Path, source: dict):
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is required for PDF extraction")
    result = subprocess.run(
        [executable, "-layout", str(path), "-"],
        capture_output=True,
        timeout=120,
        check=True,
    )
    pages = result.stdout.decode("utf-8").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    for number, page in enumerate(pages, start=1):
        yield evidence(source, {"kind": "pdf_page", "page": number}, text=page)


def chunks_for(page: dict, size: int = 1600, overlap: int = 200):
    if size <= overlap or overlap < 0:
        raise ValueError("Chunk size must exceed nonnegative overlap")
    text = page["text"]
    for start in range(0, len(text), size - overlap):
        end = min(start + size, len(text))
        if text[start:end].strip():
            yield {
                "id": stable_id("chunk", page["id"], VERSION, str(start), str(end)),
                "citation_id": page["id"],
                "source_id": page["source_id"],
                "start_char": start,
                "end_char": end,
                "text": text[start:end],
                "processing_version": VERSION,
            }
        if end == len(text):
            break


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def prepare(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if not root.is_dir():
        raise ValueError("Input must be an existing directory")
    if output == root or root in output.parents:
        raise ValueError("Output must be outside the source directory")
    # A new directory avoids silently replacing a previous evidence bundle.
    output.mkdir(parents=True, exist_ok=False)
    sources = inventory(root)
    counts: Counter = Counter()
    with (output / "citations.jsonl").open("w", encoding="utf-8") as citations, (
        output / "chunks.jsonl"
    ).open("w", encoding="utf-8") as chunks:
        for source in sources:
            path = root / source["relative_paths"][0]
            try:
                if source["extension"] == ".csv":
                    records = list(csv_records(path, source))
                    write_json(output / f"{source['id']}.table.json", {
                        "source_id": source["id"],
                        "records": records,
                        "profiles": numeric_profiles(records),
                        "header_record": None,
                        "review_required": True,
                        "processing_version": VERSION,
                    })
                    for record in records:
                        citations.write(json.dumps(record, ensure_ascii=False) + "\n")
                    counts["csv_records"] += len(records)
                    source["status"] = "table_extracted_needs_review"
                elif source["extension"] == ".pdf":
                    pages = list(pdf_pages(path, source))
                    empty = 0
                    for page in pages:
                        citations.write(json.dumps(page, ensure_ascii=False) + "\n")
                        empty += not bool(page["text"].strip())
                        for chunk in chunks_for(page):
                            chunks.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                            counts["chunks"] += 1
                    counts["pdf_pages"] += len(pages)
                    source["empty_pages"] = empty
                    source["status"] = (
                        "text_extracted_needs_review" if pages and not empty
                        else "partial_or_empty_text_needs_review"
                    )
                else:
                    source["status"] = "catalogued_parser_pending"
            except (OSError, UnicodeError, csv.Error, RuntimeError,
                    subprocess.SubprocessError) as error:
                source["status"] = "extraction_failed"
                source["error_type"] = type(error).__name__
            counts[source["status"]] += 1
    write_json(output / "sources.json", sources)
    report = {
        "processing_version": VERSION,
        "file_count": sum(len(s["relative_paths"]) for s in sources),
        "source_count": len(sources),
        "investigations": sorted({s["investigation_id"] for s in sources
                                  if s["investigation_id"]}),
        "total_file_bytes": sum(s["size_bytes"] * len(s["relative_paths"]) for s in sources),
        "counts": dict(counts),
        "published": False,
        "review_required": True,
    }
    write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
