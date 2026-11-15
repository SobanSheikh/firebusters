"""Prepare the first reviewed scientific slice, preserving source-record citations."""

import argparse
import csv
import json
import math
import re
from pathlib import Path

from openpyxl import load_workbook

from app.ingestion import evidence, inventory, stable_id, write_json

VERSION = "research-v2"
RUN_FILE = "PSI-159_Experimental table_CFI-G_Normal Flames (1).csv"
CHART_FILE = "PSI-117_Analyzed Data_PROCI_C12_2019_Three_Stage.csv"
BASS_FILE = "BASS test matrix.xlsx"

TERMINATION_LABELS = {
    "SE": "Self-extinction",
    "FT": "Flow termination",
}


def finite(value):
    normalized = "" if value is None else str(value).strip()
    if normalized.lower() in {"", "-", "n/a", "na"} or normalized.startswith("#"):
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite measurement")
    return number


def optional_finite(value):
    try:
        return finite(value)
    except (TypeError, ValueError):
        return None


def text_value(value) -> str:
    return "" if value is None else str(value).strip()


def json_cell(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def normalize_material(value) -> str:
    material = " ".join(text_value(value).split())
    material = re.sub(r"\bparrafin\b", "paraffin", material, flags=re.I)
    material = re.sub(r"\bpmma\b", "PMMA", material, flags=re.I)
    material = re.sub(r"\bsibal\b", "SIBAL", material, flags=re.I)
    material = re.sub(r"\bnomex\b", "Nomex", material, flags=re.I)
    return material


def bass_outcome(observation: str) -> tuple[str, bool]:
    """Conservatively normalize an as-run narrative; the original remains authoritative."""
    value = " ".join(observation.lower().split())
    suppression = bool(re.search(r"\b(?:n2|gn2|nitrogen)\b", value))
    if re.search(r"\b(?:no ignition|did not ignite|failed to ignite|no flame)\b", value):
        return "ignition_failed", suppression
    if suppression and re.search(
        r"\b(?:did not|does not|didn't|fails? to)\b.{0,35}\b(?:extinguish|blow out)\b"
        r"|\bno joy\b",
        value,
    ):
        return "suppression_failed", True
    if suppression and re.search(
        r"\b(?:bottom half|stagnation region|stag region|leading edge)\b.{0,30}\b(?:blew|blow)\b"
        r"|\b(?:blew|blow)\b.{0,30}\b(?:bottom half|stagnation region|stag region|leading edge)\b",
        value,
    ):
        return "suppression_partial", True
    if suppression and re.search(
        r"\bflame did blow out with (?:n2|gn2|nitrogen)\b"
        r"|\b(?:n2|gn2|nitrogen) extinguish(?:ed)? the flame\b"
        r"|\bflame (?:was )?extinguish(?:ed)? by (?:n2|gn2|nitrogen)\b",
        value,
    ):
        return "suppression_succeeded", True
    if re.search(r"\b(?:self[- ]extinguish(?:ed)?|went out on its own)\b", value):
        return "self_extinguished", suppression
    if re.search(r"\b(?:burned out|burnt out|ran out of fuel|out of wax|fuel consumed)\b", value):
        return "fuel_consumed", suppression
    if re.search(r"\b(?:air|fan|flow) (?:was |is )?(?:off|shut off|turned off)\b", value):
        return "airflow_terminated", suppression
    if re.search(r"\b(?:burn|burning|flame|spread|ignit)\w*\b", value):
        return "observed_burning", suppression
    return "unclassified", suppression


def prepare(root: Path) -> dict:
    required_files = {RUN_FILE, CHART_FILE, BASS_FILE}
    selected = {s["filename"]: s for s in inventory(root)
                if s["filename"] in required_files}
    if set(selected) != required_files:
        raise ValueError("Required reviewed sources are missing")
    citations, experiments = [], []
    source = selected[RUN_FILE]
    with (root / source["relative_paths"][0]).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "Flame Type", "Day", "Fuel", "Test", "Cool flame?", " XO2 before test",
            "XO2  after test", "approx p (bar)", "Xf", "mHC (mg/s)", "TFP", "Tad (K)",
            "Zst", "Hot ignition", "burn time (sec)", "Self-ext or flow term",
            "Peak burner T (C )", "Comments",
        }
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
            termination = row["Self-ext or flow term"].strip()
            experiments.append({
                "id": stable_id("exp", source["id"], run), "investigation_id": "PSI-159",
                "source_id": source["id"], "citation_id": citation["id"], "run": run,
                "fuel": row["Fuel"].strip(), "pressure_bar": finite(row["approx p (bar)"]),
                "burn_time_s": finite(row["burn time (sec)"]),
                "fuel_flow_mg_s": finite(row["mHC (mg/s)"]),
                "flame_type": row["Flame Type"].strip(), "day": row["Day"].strip(),
                "cool_flame": row["Cool flame?"].strip() or None,
                "oxygen_before": finite(row[" XO2 before test"]),
                "oxygen_after": finite(row["XO2  after test"]),
                "fuel_fraction": finite(row["Xf"]), "tfp": row["TFP"].strip() or None,
                "adiabatic_temperature_k": finite(row["Tad (K)"]),
                "stoichiometric_mixture_fraction": finite(row["Zst"]),
                "hot_ignition": row["Hot ignition"].strip() or None,
                "peak_burner_temperature_c": finite(row["Peak burner T (C )"]),
                "termination": termination,
                "termination_label": TERMINATION_LABELS.get(termination, "Not reported"),
                "comments": row.get("Comments", "").strip(),
                "evidence_type": "reported_experiment", "processing_version": VERSION,
            })

    source = selected[BASS_FILE]
    workbook = load_workbook(root / source["relative_paths"][0], read_only=True, data_only=True)
    if "as run matrix" not in workbook.sheetnames:
        raise ValueError("PSI-26 as-run worksheet is missing")
    sheet = workbook["as run matrix"]
    headers = [text_value(cell.value) for cell in sheet[3]]
    required_bass = {
        "Actual Date  (for SPICE Display Date, add 1 for Leap Year)", "As run test no.",
        "Test no.", "Sample no.", "material", "Fan display", "Air display", "GN2 Pot",
        "GN2 display", "O2 % by volume", "pressure, atm", "CO2, mm Hg",
        "Test Observations and Anomalies (ignited, spread, extinguished, burn time, color, etc.)",
    }
    if not required_bass.issubset(headers):
        raise ValueError("PSI-26 as-run schema differs from reviewed workbook")
    columns = {name: headers.index(name) for name in required_bass}
    for row_number, values in enumerate(sheet.iter_rows(min_row=4, values_only=True), 4):
        run_value = values[columns["As run test no."]]
        material_raw = text_value(values[columns["material"]])
        if not material_raw or not text_value(run_value).isdigit():
            continue
        material = normalize_material(material_raw)
        observation = text_value(values[columns[
            "Test Observations and Anomalies (ignited, spread, extinguished, burn time, color, etc.)"
        ]])
        outcome, suppression_attempted = bass_outcome(observation)
        date_value = values[columns["Actual Date  (for SPICE Display Date, add 1 for Leap Year)"]]
        date = date_value.date().isoformat() if hasattr(date_value, "date") else text_value(date_value)
        excerpt = {
            headers[index]: json_cell(values[index])
            for index in range(len(headers))
            if values[index] is not None
        }
        citation = evidence(
            source,
            {"kind": "xlsx_record", "sheet": "as run matrix", "record": row_number},
            excerpt=excerpt,
        )
        citations.append(citation)
        run = text_value(run_value)
        experiments.append({
            "id": stable_id("exp", source["id"], "as run matrix", str(row_number)),
            "investigation_id": "PSI-26", "source_id": source["id"],
            "citation_id": citation["id"], "run": run, "fuel": material,
            "material": material, "material_raw": material_raw, "date": date,
            "test_number": text_value(values[columns["Test no."]]) or None,
            "sample_number": text_value(values[columns["Sample no."]]) or None,
            "fan_display": text_value(values[columns["Fan display"]]) or None,
            "air_display": text_value(values[columns["Air display"]]) or None,
            "nitrogen_pot": text_value(values[columns["GN2 Pot"]]) or None,
            "nitrogen_display": text_value(values[columns["GN2 display"]]) or None,
            "oxygen_source_value": optional_finite(values[columns["O2 % by volume"]]),
            "oxygen_source_raw": text_value(values[columns["O2 % by volume"]]) or None,
            "pressure_atm": optional_finite(values[columns["pressure, atm"]]),
            "pressure_atm_raw": text_value(values[columns["pressure, atm"]]) or None,
            "co2_mm_hg": optional_finite(values[columns["CO2, mm Hg"]]),
            "co2_mm_hg_raw": text_value(values[columns["CO2, mm Hg"]]) or None,
            "observation": observation, "derived_outcome": outcome,
            "suppression_attempted": suppression_attempted,
            "normalization_note": (
                "Outcome is a conservative keyword normalization of the as-run observation; "
                "inspect the cited workbook row for the authoritative wording."
            ),
            "evidence_type": "reported_experiment_log", "processing_version": VERSION,
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
            {"id": "PSI-26", "title": "Burning and Suppression of Solids", "subtitle": "As-run solid-material fire and suppression observations"},
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
