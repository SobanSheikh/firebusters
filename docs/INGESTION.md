# Local evidence preparation

The first ingestion stage runs without credentials or network access. It produces a reviewable local evidence bundle; it does not publish data to Supabase.

From `backend/`, run:

```bash
python3 -m app.ingestion --input '../data/ nasa' --output '../data/processed/evidence-v1'
python3 -m unittest discover -s tests -p test_ingestion.py -v
```

The output directory must not already exist and must be outside the input directory. Choose a new output directory for a new run. Generated bundles under `data/processed/` are ignored by Git. Originals are read-only inputs. PDF extraction requires Poppler's `pdftotext` on the ingestion machine; the deployed API does not need it.

## Bundle contents

- `sources.json`: SHA-256, stable source ID, investigation ID, relative filename aliases, intended Storage object key, media type, extraction status, and quality flags.
- `citations.jsonl`: exact PDF pages or CSV record positions with the original extracted text/cells.
- `chunks.jsonl`: narrative text chunks referencing a stable page citation, with exact character offsets. Embeddings are a subsequent step.
- `<source-id>.table.json`: original positional CSV cells and basic numerical profiles. Duplicate headers and blank cells are preserved. CSV record numbers are logical records, not physical lines when a cell contains a newline.
- `report.json`: fresh counts, extraction outcomes, coverage, and review status.

IDs are derived from investigation and content checksum. Duplicate bytes inside an investigation share a source while retaining all filename aliases. Renaming a source does not change its ID. Changed bytes create a new version/ID. Citation IDs add a stable page or CSV-record locator. Chunks include the processing version and character range. The bundle contains no absolute local paths, credentials, or expiring signed URLs.

## Scientific review boundary

CSV extraction does not guess headers, physical units, experiment IDs, or whether a series is measured or simulated. Its numeric profiles include every finite numeric cell in a positional column; they are diagnostics, not publishable scientific statistics. Review and format-specific adapters must establish these meanings before a chart is published.

PDF extraction is text-only, without OCR; empty pages are flagged. Successful text extraction still needs review for layout/order and source fidelity. DAT, XLS/XLSX, DOCX, ZIP, and PXP are catalogued as parser pending in this first stage. No archive is extracted or scientific scale inferred.

## Supabase publication contract (next implementation stage)

1. Validate the bundle and reviewed structured adapters; verify current source checksums against the manifest.
2. Upload original bytes to the manifest's content-addressed `storage_key` in the private source bucket. Check object size/type limits before uploading.
3. Insert/upsert sources, citations, chunks, and reviewed experiment/chart records using stable IDs, with version-aware publication state.
4. Validate uploaded assets and referential integrity before marking a batch public.
5. Resolve citation IDs through an authenticated/authorized backend route into fresh signed URLs. Store stable viewer routes in boards/exports, never signed URLs.
6. Generate embeddings separately; narrative retrieval and numerical processing remain separate paths.

Database migrations, cloud upload, signed-URL routes, reviewed chart recipes, and embeddings are not implemented by this preparation command.
