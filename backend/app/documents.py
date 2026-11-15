"""Prepare a small PDF evidence bundle locally; no network or database writes."""

import argparse
from pathlib import Path

from app.ingestion import inventory, pdf_pages, write_json

FILES = {
    "PSI-159_Reports_FinalRpt_ACME.CFI-G.pdf",
    "PSI-117_Presentations_PSI_Users_Group_Cool_Flames_in_Space_03302026.pdf",
    "PSI-117_Presentations_Three_Stage_Cool_Flame_TFarouk.pdf",
}


def prepare_documents(root: Path) -> dict:
    sources = [s for s in inventory(root) if s["filename"] in FILES]
    if {s["filename"] for s in sources} != FILES:
        raise ValueError("Required PDF source is missing")
    citations = []
    for source in sources:
        pages = list(pdf_pages(root / source["relative_paths"][0], source))
        readable = [p for p in pages if p["text"].strip()]
        if not readable:
            raise ValueError(f"No extractable text: {source['filename']}")
        source["status"] = "text_extracted_needs_review"
        source["empty_pages"] = len(pages) - len(readable)
        citations.extend(readable)
    # Existing investigations are deliberately not overwritten; load research-v1 first.
    return {"version": "documents-v1", "investigations": [], "sources": sources,
            "citations": citations, "experiments": [], "charts": []}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output already exists; choose a new path")
    bundle = prepare_documents(args.input)
    write_json(args.output, bundle)
    print(f"Prepared {len(bundle['sources'])} PDFs, {len(bundle['citations'])} nonempty pages; not published.")
