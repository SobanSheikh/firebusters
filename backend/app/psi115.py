"""Strict PSI-115 numerical extraction; physical mapping requires review."""

import argparse
import gzip
import json
import math
from pathlib import Path

from app.ingestion import digest, evidence, inventory, write_json

VERSION = "psi115-v1"


def number(token: str) -> float:
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError("Nonfinite numerical value")
    return value


def parse_grid(path: Path) -> dict:
    with path.open() as handle:
        header = handle.readline().split()
        if len(header) != 4:
            raise ValueError("Expected four integer header entries")
        shape = [int(item) for item in header]
        if any(value <= 0 for value in shape) or shape[2:] != [1, 1]:
            raise ValueError("Only positive two-dimensional scalar headers are supported")
        expected = math.prod(shape)
        if expected > 2_000_000:
            raise ValueError("Grid exceeds parser limit")
        values = []
        for line in handle:
            for token in line.split():
                values.append(number(token))
                if len(values) > expected:
                    raise ValueError(f"Extra value: header expects {expected}; no values discarded")
        if len(values) != expected:
            raise ValueError(f"Truncated grid: expected {expected}, found {len(values)}")
    return {"kind": "scalar_grid", "header": shape, "values": values}


def parse_distribution(path: Path) -> dict:
    records = []
    seen = set()
    with path.open() as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            cells = line.split()
            if len(cells) != 2:
                raise ValueError(f"Expected node ID and value at line {line_number}")
            node = int(cells[0])
            if node < 1 or node in seen:
                raise ValueError(f"Invalid or duplicate node at line {line_number}")
            seen.add(node)
            records.append({"node": node, "value": number(cells[1]), "line": line_number})
    if not records:
        raise ValueError("Empty distribution")
    return {"kind": "node_distribution", "records": records}


def parse_diameters(path: Path) -> dict:
    with path.open() as handle:
        label = handle.readline().strip()
        if label != "Diameter (starting from first non-vapor node)":
            raise ValueError("Unrecognized diameter header")
        values = [number(token) for line in handle for token in line.split()]
    if not values or any(v <= 0 for v in values):
        raise ValueError("Diameters must be positive")
    if any(a >= b for a, b in zip(values, values[1:])):
        raise ValueError("Diameters must increase strictly")
    # Do not guess how the first diameter maps to PSD nodes 1 or 2.
    return {"kind": "diameters", "header_label": label, "values": values}


def index_preview(values: list[float], bins: int = 400) -> list[dict]:
    """Bounded min/max envelopes preserve extremes without inventing spatial axes."""
    if bins < 1:
        raise ValueError("Positive bin count required")
    step = max(1, math.ceil(len(values) / bins))
    result = []
    for start in range(0, len(values), step):
        block = values[start:start + step]
        result.append({"start_index": start, "end_index_exclusive": start + len(block),
                       "min": min(block), "max": max(block)})
    return result


def prepare_fields(root: Path, output: Path) -> dict:
    root, output = root.resolve(), output.resolve()
    if not root.is_dir() or root.name != "PSI_115":
        raise ValueError("Input must be the PSI_115 directory")
    if output == root or root in output.parents:
        raise ValueError("Output must be outside source directory")
    output.mkdir(parents=True, exist_ok=False)
    # Inventory from the parent retains the exact source IDs used by ingestion.
    sources = [s for s in inventory(root.parent) if s["investigation_id"] == "PSI-115"
               and s["extension"] == ".dat"]
    records = []
    for source in sources:
        path = root.parent / source["relative_paths"][0]
        record = {"source_id": source["id"], "filename": path.name,
                  "source_sha256": source["sha256"], "parser_version": VERSION,
                  "evidence_type": "simulation", "review_required": True,
                  "publishable": False, "physical_unit": None,
                  "coordinate_mapping": None}
        try:
            if path.name == "nodeDiameters.dat":
                parsed = parse_diameters(path)
            elif "PSD" in path.stem:
                parsed = parse_distribution(path)
            else:
                parsed = parse_grid(path)
            values = parsed.get("values")
            if values is None:
                values = [r["value"] for r in parsed["records"]]
            citation = evidence(source, {"kind": "dataset_file", "selection": "all_values"})
            artifact = {**record, **parsed, "citation": citation,
                        "transformation": "Numeric parsing only; original file order and scale"}
            payload = json.dumps(artifact, allow_nan=False, separators=(",", ":")).encode()
            artifact_path = output / f"{source['id']}.json.gz"
            artifact_path.write_bytes(gzip.compress(payload, mtime=0))
            record.update({"status": "parsed_needs_review", "kind": parsed["kind"],
                           "count": len(values), "min": min(values), "max": max(values),
                           "citation": citation, "artifact": artifact_path.name,
                           "artifact_sha256": digest(artifact_path),
                           "index_preview": index_preview(values)})
            if "header" in parsed:
                record["header"] = parsed["header"]
        except (ValueError, OSError) as error:
            record.update({"status": "validation_failed", "reason": str(error)})
        records.append(record)
    write_json(output / "fields.json", records)
    report = {"parser_version": VERSION, "files": len(records),
              "parsed": sum(r["status"] == "parsed_needs_review" for r in records),
              "failed": sum(r["status"] == "validation_failed" for r in records),
              "publishable": False,
              "limitations": ["Spatial ordering and physical coordinates not established",
                              "No physical unit conversion or PSD/diameter join applied",
                              "Extra values rejected, never truncated"]}
    write_json(output / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare_fields(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
