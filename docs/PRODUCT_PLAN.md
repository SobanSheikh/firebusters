# Firebusters product plan

## Immediate goal: local hackathon presentation MVP

The presentation MVP uses only the NASA files currently downloaded in `data/ nasa/`:

- 141 files
- Approximately 388 MB
- 10 PSI investigation folders
- PDFs, DAT grids, CSV, ZIP, XLS/XLSX, PXP and DOCX files

No additional NASA archive download is required for this milestone.

### MVP architecture

```text
Local ingestion scripts
        │
        ├── Supabase Storage (private source and derived files)
        └── Supabase PostgreSQL + pgvector
                    │
                    ▼
             Render FastAPI API
                    │
                    ▼
              Vercel React UI
```

### MVP product promise

Firebusters lets a judge explore the currently available microgravity-combustion evidence, compare a few representative experiments, and trace every result back to a NASA source.

### MVP features

1. **Investigation library**
   - Browse the 10 locally available PSI investigation groups.
   - Show title, summary, file count, source types and available evidence.

2. **Evidence search**
   - Search extracted document text and investigation metadata.
   - Return source-aware snippets rather than uncited generated prose.

3. **Citation viewer**
   - Cite PDF page/section, spreadsheet sheet/range, dataset/run, or video timestamp.
   - Open a short-lived signed URL to the private source file in Supabase Storage.

4. **Two presentation stories**
   - Cool flames: PSI-117 and PSI-159 reports/presentations.
   - Gravity comparison: representative PSI-115 numerical fields, summarized locally.

5. **Simple comparison visualization**
   - Render precomputed summary statistics or heatmap artifacts.
   - Show the exact source files and transformations beneath every chart.

6. **Health and graceful degradation**
   - The library, evidence and charts work without an LLM.
   - Groq-assisted synthesis is optional and enabled only after a key is configured.

### One-day ingestion scope

Catalog all 141 files, but process them at different depths:

| Tier | Content | Treatment |
| --- | --- | --- |
| A | PSI-117 and PSI-159 reports/presentations | Extract, chunk, cite and index |
| A | Selected PSI-115 DAT fields | Compute summaries and presentation artifacts |
| B | PSI-39, PSI-98 and overview/safety documents | Extract metadata and useful text/tables |
| C | Remaining files and archives | Catalog with manifest, checksum and storage link |

This keeps the demo credible without pretending every scientific format has already been fully interpreted.

### MVP ingestion flow

1. Inventory files and calculate SHA-256 checksums.
2. Assign stable source IDs and PSI investigation IDs.
3. Upload original files to the private `firebusters-assets` Supabase Storage bucket.
4. Extract Tier A/B document text locally with page-aware locators.
5. Normalize selected tables and numerical summaries locally.
6. Upload compact records, chunks, citations and statistics to PostgreSQL.
7. Generate embeddings only for useful narrative chunks; never embed every numerical row.
8. Validate that every searchable chunk resolves to a source locator.

### MVP acceptance criteria

- Render `/api/v1/health` reports API and database healthy.
- The frontend loads from Vercel and can call Render without CORS errors.
- A judge can browse at least two investigations.
- At least two guided stories work without live AI generation.
- Every displayed claim/chart has a resolvable citation.
- No response requires reading files from Render's ephemeral filesystem.

## Extensive product plan

The extensive version expands ingestion and uses multiple storage sources behind one asset abstraction.

### Storage strategy

| Storage | Use |
| --- | --- |
| Supabase PostgreSQL | Investigations, experiments, chunks, citations, manifests, vectors and compact statistics |
| Supabase Storage | MVP documents, thumbnails and small presentation assets |
| Cloudflare R2 | Large videos, Parquet, grids, image sequences and long-term derived artifacts |
| NASA public URLs | Canonical source links; avoid mirroring when reliable direct access is enough |
| Local workspace | Raw download staging and heavy ingestion only |

All assets use a common manifest with `provider`, `bucket`, `object_key`, canonical NASA URL, checksum, MIME type, size, ingestion version and citation metadata. The frontend never depends on a provider-specific URL; the API resolves assets and generates signed links.

### Extensive ingestion

- Incremental discovery of additional PSI investigations.
- Format-specific parsers with validation reports.
- Experiment/run grouping and scientific-unit normalization.
- Parquet conversion and tiled previews for large grids.
- Video scene/frame extraction and timestamp citations.
- Idempotent ingestion jobs with resumable manifests.
- Data-quality flags and human review queues.
- Versioned derivations so charts can be reproduced.

### Extensive product features

- Hybrid semantic, keyword and structured search.
- Agent tools for experiment comparison and evidence synthesis.
- Interactive parameter filters and linked visualizations.
- Reproducible chart recipes and downloadable evidence packs.
- Investigation timelines and cross-mission comparison.
- Authenticated curator workflow for correcting metadata.
- Optional durable job queue when remote ingestion becomes necessary.

### Migration trigger from Supabase Storage to R2

Add R2 when any of these becomes true:

- Supabase Storage approaches its free quota.
- Individual source/derived files exceed the practical upload limit.
- Video, grids or Parquet become central to the product.
- Public asset egress becomes material.

The manifest abstraction makes this a per-object migration rather than an application rewrite.
