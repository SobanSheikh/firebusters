# First working research workflow

This slice implements PSI-159 normal-flame experiment browsing and a PSI-117 experimental droplet-history chart. It is not the complete product plan.

## Data contract

- PSI-159: 179 reported records. Preserve run ID, fuel, approximate pressure in bar, fuel flow in mg/s, burn time in seconds, termination code, and comments. Missing values remain null. Each record cites its original logical CSV record.
- PSI-117: 205 points from the `EXPT` block of `PROCI_C12_2019_Three_Stage.csv`, columns 2–3. X is normalized time `t/D₀²` in s/mm²; Y is `(D/D₀)²`, dimensionless. Negative times are retained. Values are sorted only for drawing; original CSV record numbers remain attached. No simulated series, smoothing, physical-time conversion, or automatic stage boundaries are introduced.
- Source IDs are content-addressed and match the general ingestion pipeline. Every chart point and experiment resolves to a stable citation.

## Schema

Migration `001_research` creates `fb_investigations`, `fb_sources`, `fb_citations`, `fb_experiments`, and `fb_charts`. Foreign keys protect source and citation relationships. Unique source checksums prevent duplicate source versions within an investigation. Experiment fuel and investigation IDs are indexed.

The initial schema uses typed relational identity/reference columns with versioned JSONB scientific payloads. Original files are referenced by Storage key; compact chart points live in the chart payload. Large field arrays remain separate assets. Dedicated measurement/condition tables, vectors, boards, and curator workflows will be added with later migrations in the same MVP.

RLS is enabled and public/anon/authenticated table access is revoked. The API uses its server-side database connection. Do not supply this database credential to the browser.

## Local preparation and loading

The existing `firebusters-api:dev` image supplies the Python dependencies. `--env-file /dev/null` selects local development defaults instead of the repository's production secrets.

```bash
docker compose --env-file /dev/null up -d --no-build db api
docker compose --env-file /dev/null exec -T api alembic upgrade head
docker compose --env-file /dev/null exec -T api python -m app.research_data --input '/app/data/ nasa' --output /tmp/firebusters-research-v1.json
docker compose --env-file /dev/null exec -T api python -m app.publish_research --bundle /tmp/firebusters-research-v1.json --input '/app/data/ nasa'
```

Preparation refuses to overwrite a bundle; choose a new output filename when regenerating it. Repeating the load of an existing bundle is idempotent. Local publication refuses database hosts other than localhost, 127.0.0.1, or the Compose `db` hostname. The publisher does not automatically run migrations.

From `frontend/`:

```bash
VITE_API_BASE_URL=http://localhost:8001/api/v1 bun run dev --port 5173 --strictPort
```

The source route serves checksum-verified local originals only when `ENVIRONMENT=development`. `NASA_DATA_ROOT` can override the Docker default `/app/data/ nasa` for non-Docker development. Production resolves fresh signed URLs instead.

## API and UI

- `GET /api/v1/research/overview`: active investigations, fuels, experiment count, and compact chart data.
- `GET /api/v1/research/experiments`: fuel filtering and bounded pagination.
- `GET /api/v1/research/citations/{id}`: original excerpt, locator, filename, checksum, and stable source route.
- `GET /api/v1/research/sources/{id}`: original source download, resolved locally in development or through private Storage in production.

UI: fuel filter, paginated experiment table, up-to-four-record descriptive comparison, experimental chart, keyboard-operable point slider, source drawer, original-file downloads, explicit loading/error/empty states, and responsive layouts.

## Cloud publication boundary

Migration `001_research` and the selected-source publication have now been applied to Supabase with approval. The cloud database contains 2 sources, 179 experiments, 384 citations, and one 205-point chart. For subsequent reviewed batches, apply any required migration with the intended database connection, then run `app.publish_research` with `--upload` and the configured Supabase URL, secret key, and private bucket. This flag performs external writes: uploads content-addressed source objects, verifies downloaded bytes, and transactionally upserts database records. It never overwrites an existing object. A failed DB transaction may leave an unreferenced content-addressed object; rerunning re-verifies and reuses it.

Production asset rows become storage-verified only after checksum verification. Signed URLs expire after five minutes and are generated on each source request. No secret or expiring URL is stored in frontend state as a permanent citation.

Live cloud acceptance passed: both uploaded source checksums match; production source-resolution code generated valid signed links twice per source; anonymous public downloads were blocked; all five tables have RLS enabled and SELECT privileges denied to anon/authenticated roles; a chart citation resolved correctly. Expiry-boundary testing was not performed. Render and Vercel application code has not been redeployed.

## Completed validation

- Four normalization tests cover unknown schemas, incomplete pairs, nonfinite values, missingness, units, and citations after sorting.
- Local migration applied successfully.
- Same bundle loaded twice: still 179 experiments and 205 chart points.
- Local HTTP checks passed for filtering, pagination, citation retrieval, original-file checksum, chart-record locators, missing citation 404, and invalid query 422.
- Frontend production build and lint passed. Chart code splitting reduced the main JavaScript bundle from 734 KB to 363 KB, with a separate 372 KB chart chunk.
- No automated browser visual or accessibility audit has been completed yet.

The publisher now batches upserts to avoid sequential network round trips; a local repeat load passed after this change. Alembic configuration escapes percent-encoded database URLs correctly.

Next: implement evidence search and the research assistant, complete focused browser review, and extend the remaining product features. Production code deployment remains separate from the completed cloud data publication.
