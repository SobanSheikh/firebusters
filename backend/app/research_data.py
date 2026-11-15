"""Prepare the first reviewed scientific slice, preserving source-record citations."""

import argparse
import csv
import json
import math
from pathlib import Path

from app.ingestion import evidence, inventory, stable_id, write_json

VERSION = "research-v1"
RUN_FILE = "PSI-159_Experimental table_CFI-G_Normal Flames (1).csv"
CHART_FILE = "PSI-117_Analyzed Data_PROCI_C12_2019_Three_Stage.csv"


def finite(value: str):
    if not value.strip():
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite measurement")
    return number


def prepare(root: Path) -> dict:
    selected = {s["filename"]: s for s in inventory(root)
                if s["filename"] in {RUN_FILE, CHART_FILE}}
    if set(selected) != {RUN_FILE, CHART_FILE}:
        raise ValueError("Required reviewed sources are missing")
    citations, experiments = [], []
    source = selected[RUN_FILE]
    with (root / source["relative_paths"][0]).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"Test", "Fuel", "approx p (bar)", "burn time (sec)", "mHC (mg/s)"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("PSI-159 header differs from reviewed schema")
        seen = set()
        for row_number, row in enumerate(reader, 2):
            if not any(v and str(v).strip() for v in row.values()):
                continue
            if None in row:
                raise ValueError("Unexpected additional CSV columns")
            run = row["Test"].strip()
            if not run or run in seen:
                raise ValueError(f"Missing or duplicate run at record {row_number}")
            seen.add(run)
            citation = evidence(source, {"kind": "csv_record", "record": row_number},
                                excerpt=row)
            citations.append(citation)
            experiments.append({
                "id": stable_id("exp", source["id"], run), "investigation_id": "PSI-159",
                "source_id": source["id"], "citation_id": citation["id"], "run": run,
                "fuel": row["Fuel"].strip(), "pressure_bar": finite(row["approx p (bar)"]),
                "burn_time_s": finite(row["burn time (sec)"]),
                "fuel_flow_mg_s": finite(row["mHC (mg/s)"]),
                "termination": row.get("Self-ext or flow term", "").strip(),
                "comments": row.get("Comments", "").strip(),
                "evidence_type": "reported_experiment", "processing_version": VERSION,
            })
    source = selected[CHART_FILE]
    with (root / source["relative_paths"][0]).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if rows[0][1:3] != ["t/(Do)2 (s/mm2)", "(D/Do)2"] or rows[1][0] != "EXPT":
        raise ValueError("PSI-117 experimental block differs from reviewed schema")
    points = []
    for number, row in enumerate(rows[1:], 2):
        x, y = row[1:3]
        if not x.strip() and not y.strip():
            continue
        if not x.strip() or not y.strip():
            raise ValueError(f"Incomplete experimental pair at record {number}")
        citation = evidence(source, {"kind": "csv_record", "record": number,
                                    "columns": [2, 3]},
                            excerpt={rows[0][1]: x, rows[0][2]: y})
        citations.append(citation)
        points.append({"x": finite(x), "y": finite(y), "record": number,
                       "citation_id": citation["id"]})
    if any(p["y"] < 0 for p in points):
        raise ValueError("Negative squared diameter")
    # Sort solely for chart rendering; retain original record numbers and do not smooth.
    points.sort(key=lambda p: p["x"])
    chart = {
        "id": "psi117-three-stage-droplet-history", "investigation_id": "PSI-117",
        "source_id": source["id"], "title": "Three-stage combustion: droplet history",
        "evidence_type": "experimental_series", "processing_version": VERSION,
        "x_label": "Normalized time t/D₀²", "x_unit": "s/mm²",
        "y_label": "Normalized squared diameter (D/D₀)²", "y_unit": "dimensionless",
        "points": points,
        "method": "CSV EXPT block, columns 2–3. Sorted by normalized time; no smoothing or interpolation.",
        "limitations": "Negative times are retained from the source. This chart does not identify combustion-stage boundaries or mix in simulation columns.",
    }
    return {
        "version": VERSION,
        "investigations": [
            {"id": "PSI-159", "title": "Cool Flames Investigation with Gases", "subtitle": "Reported normal-flame experiment conditions"},
            {"id": "PSI-117", "title": "Cool-flame droplet combustion", "subtitle": "Selected experimental droplet-history series"},
        ],
        "sources": list(selected.values()), "citations": citations,
        "experiments": experiments, "charts": [chart],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a new output file")
    bundle = prepare(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, bundle)
    print(json.dumps({key: len(bundle[key]) for key in
                      ["investigations", "sources", "citations", "experiments", "charts"]}))


if __name__ == "__main__":
    main()
