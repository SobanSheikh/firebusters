# Firebusters: judged MVP product and delivery plan

Status: approved scope direction; implementation plan, not a claim of completed features.

This plan supersedes the earlier narrow presentation MVP. The judged release includes the complete user experience below. The next phase expands data coverage and changes infrastructure where needed; it does not defer the core product features.

## 1. Product promise

Firebusters turns NASA combustion research into an interactive workspace where people can discover experiments, explore real data, compare findings, ask scientific questions, and produce a traceable research brief.

Primary users are students, science educators, and researchers exploring an unfamiliar investigation. Judges should understand the value within the first minute and verify a finding without leaving the workspace.

The central journey is:

**Question → relevant investigations → interactive comparison → explanation → source evidence → saved/exported brief.**

Our presentation thesis is that complex NASA evidence becomes understandable and reusable when explanation, numerical analysis, and citations share one interface. Visual polish supports this journey; scientific traceability earns trust. No award outcome is guaranteed.

## 2. Release boundary

- Build every feature area in this plan for the judged MVP, with complete supported workflows and no decorative dead ends.
- Use the current local dataset in `data/ nasa/`. The previous inventory records 141 files, approximately 388 MB, and 10 PSI investigation folders; re-inventory before publishing counts.
- No additional raw archive download is required for this release.
- Use Vercel, Render, Supabase PostgreSQL/pgvector, and private Supabase Storage.
- Use Groq for generation now, retaining provider configuration for Gemini later.
- Run extraction, numerical preprocessing, and ingestion locally.
- Work on `dev`; release to production through a reviewed merge to `main`.
- Verify production branch settings on both platforms. Vercel preview deployments may still run for development branches and are distinct from production deployments.
- This document is authoritative for product scope. `ARCHITECTURE.md` describes deployment history; `RESOURCE_PRIORITY.md` informs data selection but does not override this release boundary.

## 3. Dashboard and interaction design

Use a coherent mission-control visual language: deep neutral backgrounds, warm flame accents, cool scientific-field colors, readable typography, and restrained motion. Data visualization must remain legible without relying on color alone.

The dashboard should answer three questions immediately: what can I explore, what can I learn, and where did the evidence come from?

| Workspace | Primary interaction | Useful outcome |
| --- | --- | --- |
| Mission Control | Start a guided investigation or resume a board | Reach meaningful evidence in one action |
| Investigation Explorer | Search, filter, inspect, and select experiments | Find relevant data and understand coverage |
| Comparison Lab | Compare compatible runs and manipulate linked charts | Understand differences and limitations |
| Ask Firebusters | Ask a question and inspect returned evidence/charts | Obtain a supported explanation |
| Stories & Impact | Navigate science stories, incident timelines, and relationships | Connect research with practical relevance |
| Research Board | Save findings, annotate, share, and export | Leave with a reproducible evidence brief |
| Curator workspace | Review metadata and ingestion quality | Correct and maintain the evidence base |

Shared UI: navigation, global search, active investigation context, comparison tray, citation drawer, source viewer, and keyboard-accessible controls. Dashboard metrics must come from the ingested catalog. Avoid invented activity feeds, unsupported safety scores, and arbitrary confidence percentages.

## 4. Complete MVP feature specification

### A. Mission Control dashboard

- Show verified investigation, source, experiment, and searchable-document counts with coverage definitions.
- Feature Gravity Lens, Cool Flames, and Spacecraft Fire Lessons entry cards.
- Offer useful example questions and explain which source collection supports each.
- Show recent boards for the current user/device and an immediately usable guest path.
- Provide a small, interactive scientific preview tied to a real dataset; label any decorative animation as an illustration.
- Include a presentation mode with larger labels, hidden editing controls, and an obvious reset action.

Acceptance: a first-time visitor can start a supported exploration without authentication or instructions from the presenter.

### B. Investigation and experiment explorer

- Catalog every current file and investigation, including sources that cannot yet be parsed.
- Filter by available metadata: investigation, research topic, fuel/material, environment, evidence type, and processing status.
- Show experimental conditions, diagnostics, reports, available runs, DOI/canonical NASA links, and documented relationships.
- Support table and card views, experiment selection, and adding selected items to the comparison tray.
- Distinguish downloadable source, searchable text, structured measurements, simulation fields, and unavailable raw assets.
- Display unknown values as unknown; never derive experiment counts from filenames without validation.

Acceptance: a filter selection produces traceable records, and an unavailable asset explains the limitation rather than opening a broken viewer.

### C. Comparison Lab and Gravity Lens

- Compare two to four selected records in a condition/measurement table, with units and provenance.
- Provide linked time-series/profile charts, hover inspection, series selection, zoom/reset, and meaningful parameter filters for available data.
- Build a side-by-side PSI-115 field explorer after validating file headers, coordinates, field definitions, and boundary conditions.
- Support synchronized pan/zoom, field selector, consistent color scales, and a difference view only where coordinate grids and physical quantities are compatible.
- If the files contain only snapshots, show snapshot selection; time playback requires actual time-resolved data.
- Present PSI-115 as simulation evidence unless the files establish otherwise. Do not describe smoke fields as measured flame images.
- Show numerical summaries computed by deterministic code, with source runs, units, transformation version, and missing-data treatment.
- Allow users to pin a chart and its interpretation to a board.
- Support cross-investigation descriptive comparisons while blocking unsupported numerical subtraction or causal claims.

Acceptance: at least one real field comparison and one real numerical profile/time-series workflow operate end to end. Dataset validation determines their precise quantities. A mismatch produces an explanation, not a misleading chart.

### D. AI research assistant with analysis tools

- Combine keyword/semantic retrieval with structured experiment lookup.
- Provide bounded tools for finding sources, filtering experiments, comparing compatible runs, retrieving validated chart specifications, and drafting a cited brief.
- Allow a user to ask a question about the current chart or selected experiments.
- Return structured answers containing findings, citations, relevant experiments, chart references, limitations, and follow-up suggestions.
- Stream progress such as "Finding matching experiments" and "Checking source pages"; do not expose hidden reasoning.
- Validate citation IDs and numerical references before showing an answer. Numerical claims must come from a cited source or deterministic calculation.
- Treat source text as evidence, never as tool instructions. Restrict tools to approved read-only queries; no arbitrary generated SQL or code execution.
- Limit requests, tool iterations, output size, and provider timeouts. Cancel stale requests and show recoverable failures.
- Preserve search, charts, and stories if generation fails. Clearly identify curated/precomputed explanations when used as a fallback.

Acceptance: the assistant completes question → evidence → comparison/chart → cited explanation, and responds honestly to an unsupported question.

### E. Citation drawer and source viewer

- Open citations from answers, charts, stories, and exports in the same drawer.
- Show a supporting excerpt and exact locator: PDF page, spreadsheet sheet/range, dataset run/field, or source section.
- Provide PDF page navigation, table excerpts, and appropriate file download fallbacks.
- Include original filename, investigation ID, evidence type, canonical URL/DOI when available, and transformation details for derived results.
- Use short-lived signed URLs for private assets and refresh expired links.
- Keep stable source/citation IDs in saved boards and exports; never persist expiring URLs as permanent citations.
- Timestamp citations are supported only if actual video and validated timestamps are present.

Acceptance: every material scientific claim and chart resolves to supporting evidence; original and derived evidence remain distinguishable.

### F. Guided stories, relationships, and impact

- Cool Flames: explain the phenomenon through validated PSI-117/PSI-159 material and selected numerical evidence.
- Gravity and Smoke: guide users through validated PSI-115 simulation fields and explain their interpretation limits.
- Spacecraft Fire Lessons: connect available safety material to research questions and detection/material concerns.
- Include an interactive relationship map of investigations, topics, facilities, publications, and documented applications. Selecting a node opens supporting evidence; selecting an edge explains the relationship.
- Include a source-backed timeline where dates are documented. Unknown dates remain unknown.
- Distinguish historical incidents, laboratory experiments, simulations, and technology-transfer examples.
- Treat thematic links to incidents/spinoffs as thematic, not documented causal lineage.
- Use only locally available supporting content for ingestion. Previously supplied NASA URLs may appear as external references; unsaved page contents require retrieval and verification before being summarized as evidence.
- Each story has a short guided route, optional deeper exploration, citations, and a route to the comparison workspace or assistant.

Acceptance: all three routes work without live generation, and the relationship map is navigable using keyboard and an equivalent list view.

### G. Research boards, sharing, and exports

- Let guests pin experiments, charts, cited answers, and source excerpts to a browser-local board.
- Support personal notes, ordering, removal, and restoration on the same device.
- Offer optional Supabase authentication for cloud-saved boards; the public discovery journey remains accessible without login.
- Allow the owner to create and revoke an explicit read-only share link. Private boards are private by default.
- Store chart selections/filters and source IDs so a saved finding can be reopened.
- Export a printable research brief/PDF, chart PNG, selected normalized CSV, and an evidence manifest containing source IDs, locators, checksums, units, and processing versions.
- Use browser print-to-PDF and client-side chart export where practical to reduce backend load.
- Mark user notes and AI synthesis separately from NASA statements. Protect CSV exports against formula injection.

Acceptance: a guest can build and export a brief; an authenticated owner can save, reopen, share, and revoke a board without exposing another user's private data.

### H. Curator and data-quality workflow

- Provide a small authenticated curator workspace with explicit server-side role checks.
- Review catalog entries, extraction failures, missing units, uncertain mappings, duplicate sources, and unsupported formats.
- Correct metadata and record who changed what and when; keep the original source immutable.
- Review or reject curated stories and derived chart records before public release.
- Display ingest version and refresh status. Heavy reprocessing continues through local scripts.
- Make ingestion resumable and idempotent using checksums, stable IDs, processing versions, and a dry-run manifest.

Acceptance: a curator can review and correct a record, ordinary users cannot, and repeating an ingestion does not duplicate the catalog.

## 5. Data validation and ingestion

The present inventory and earlier resource notes are starting points, not verified scientific schemas. Before implementing each chart, inspect its actual file structure and report documentation.

| Source group | Planned use | Required validation |
| --- | --- | --- |
| PSI-159 | Experiment explorer, condition tables, cited explanations | Identify actual sheets, run IDs, units, report context, and available versus absent raw files |
| PSI-117 | Cool-flame profiles/time series and story | Confirm supported formats, quantities, time axes, and experimental versus model series |
| PSI-115 | Gravity/smoke field comparison | Confirm grid dimensions, variables, coordinates, units, gravity cases, and comparable boundary conditions |
| PSI-142 | Extinction/profile comparison | Confirm available numeric tables, conditions, and compatible series |
| PSI-10 and supporting investigations | Catalog, structured discovery where possible, evidence relationships | Verify metadata and experiment counts against source contents |
| Guide, reports, and saved safety/impact material | Explanations, stories, timeline, and citations | Preserve page/section locators and distinguish historical context from current research |

Ingestion sequence:

1. Inventory every file; calculate SHA-256; detect duplicates, archives, and actual file types.
2. Assign stable investigation, source, asset, experiment, and citation identifiers.
3. Inspect archive contents safely with size/path limits; keep original assets immutable.
4. Extract documents with page/sheet/section locators and flag scanned or failed extraction.
5. Normalize experiment conditions and measurements with units, evidence types, and explicit unknown values.
6. Parse supported numerical formats; record parser versions and reproducible chart recipes.
7. Validate representative numerical outputs against original rows/fields and known dimensions.
8. Upload originals and compact derived artifacts to private Supabase Storage after checking account and per-object limits.
9. Store metadata, narrative chunks, citations, experiment records, relationships, and compact summaries in PostgreSQL.
10. Embed useful narrative text using one verified embedding model/dimension. Use SQL and numerical artifacts for measurements, not embeddings of every numeric row.
11. Check every citation and publish a coverage/quality manifest.
12. Re-run ingestion to prove safe resume and duplicate prevention.

Unsupported formats remain catalogued with an honest explanation. Availability of a feature does not imply every investigation contains data for it. If a planned hero dataset fails validation, choose another validated dataset from the current collection and document the substitution; do not invent missing measurements.

## 6. Implementation architecture

Frontend: existing React/TypeScript/Vite app, React Router, TanStack Query, Zustand, Tailwind, and Recharts. Use Canvas for dense field rendering with precomputed/downsampled assets. Add dependencies only where existing tools cannot deliver the interaction well.

Backend: FastAPI with typed contracts for catalog/search, experiments/comparisons, chart recipes, citations/assets, assistant sessions, boards/shares, and curator review. Use bounded queries, pagination, explicit error responses, and provider-independent answer schemas.

Persistence: Supabase PostgreSQL/pgvector for searchable and structured data; Supabase Storage for originals and derived assets; Supabase Auth for saved boards and curator access. Validate authentication on the API, enforce ownership/roles, and apply row-level policies wherever browser access is permitted.

Core entities: investigations, sources, assets, experiments, conditions, measurements, chunks, citations, derivations, chart recipes, relationships, stories, boards, board items, shares, ingestion runs, and metadata revisions.

Each asset records provider, bucket/object key, MIME type, size, checksum, canonical source URL when available, and processing version. Consumers use stable asset IDs; the backend resolves storage URLs.

The web service handles lightweight queries and generation. Local scripts handle extraction, numerical transformations, embedding batches, and uploads. Boards and publication state are durable in PostgreSQL. No web request starts a long ingestion job.

## 7. Build order and release gates

These are implementation stages within one complete release, not features deferred to a later product phase. Estimate delivery time after the first data audit and working vertical slice.

| Stage | Deliverable | Exit gate |
| --- | --- | --- |
| 1. Evidence contract | Fresh inventory, parser samples, supported quantities, source schema, chart recipes | Two validated numerical workflows and document citations identified |
| 2. Working vertical slice | One ingested investigation → API → dashboard → chart → citation | Real data renders from deployed services with no mock dependency |
| 3. Explorer and lab | Catalog, filters, experiment records, Gravity Lens, linked charts | Compatible comparisons work; invalid ones are explained |
| 4. Research assistant | Hybrid search, bounded tools, streaming, evidence validation | Answers and charts cite resolvable evidence; provider failure handled |
| 5. Stories and map | Three guided routes, relationships, source-backed timeline | Narratives and navigation verified against evidence |
| 6. Boards and curation | Guest boards, authentication, cloud save/share/revoke, exports, review | Ownership, export fidelity, and curator permissions verified |
| 7. Presentation polish | Responsive layouts, keyboard access, reduced motion, loading/error states | Complete judge journey rehearsed on production |
| 8. Release | Reviewed dev changes, approved data state, production smoke test | All release criteria below pass |

## 8. Quality and acceptance criteria

- Every named feature area above has a functioning end-to-end workflow; no placeholder buttons in the judged path.
- Every current investigation is catalogued; UI coverage labels reflect actual processing status.
- At least two validated numerical workflows exist, including the validated field comparison or a documented replacement from current data.
- Chart axes, field legends, units, provenance, and missing values are visible and correct.
- Scientific sources, derived calculations, AI interpretations, and user annotations are distinguishable.
- Citation links survive reload, board sharing, and signed-URL expiry.
- A small evaluation set covers at least 20 questions: source lookup, numerical comparisons, synthesis, missing evidence, and misleading premises. Review factual support, citation correctness, and numerical consistency.
- Run focused parser tests, API/permission tests, frontend build/lint, and browser end-to-end tests for explore → compare → ask → cite → save/export.
- Verify empty datasets, extraction errors, unavailable generation, expired asset links, rejected comparisons, and narrow-screen layouts.
- Test keyboard navigation, visible focus, readable contrast, accessible chart descriptions, and reduced motion.
- Target warm-service catalog/chart interactions within two seconds on a typical connection; measure and report actual results. Stream assistant status promptly and display a timeout with usable fallback.
- Keep field assets bounded/downsampled; avoid sending full high-resolution grids in the initial page response.
- Verify account storage/egress budgets before uploads; do not assume a free quota from total local file size alone.
- Protect secrets, parameterize database queries, authorize private reads/writes, and rate-limit public generation.
- Confirm production CORS and database health; exercise the frontend against the actual production API.
- Warm Render before judging. Cached stories and already-loaded charts remain usable during transient backend/provider failures; do not promise full offline functionality.

## 9. Judge demonstration: approximately five minutes

1. Open Mission Control and explain the question: how can a user learn from NASA combustion evidence and verify the answer?
2. Enter Gravity Lens, select a documented case, inspect the relevant field, and reveal its comparison. State clearly whether this is simulation or experimental evidence.
3. Ask the assistant to explain the selected result. Open a citation and show the supporting source and calculation provenance.
4. Switch to Cool Flames, filter actual records, and explore a measured/processed series with its conditions.
5. Open a related research/safety story and one documented relationship to explain the practical relevance without claiming unsupported causality.
6. Pin findings to a board and export the research brief with citations and chart metadata.
7. Show the coverage boundary and the curated fallback briefly to demonstrate reliable, honest behavior.

Prepare a shorter three-minute route and a locally recorded backup walkthrough. Any recording or curated answer is clearly identified as such.

These are presentation objectives, not a claim about official judging categories. Verify the official challenge requirements and rubric before final submission and map delivered artifacts to the actual wording.

## 10. Next phase: scale the evidence and infrastructure

After the judged release, expand NASA investigations, raw camera streams, sensor records, and numerical coverage. Extend format adapters and existing viewers to those assets.

Move large assets to R2 or another storage provider when verified object-size, capacity, or egress requirements justify it. Migrate the API platform if runtime, availability, or budget requirements justify it. Add durable workers only when remote ingestion or long-running analysis becomes necessary.

The stable source/asset IDs and storage resolver keep these changes behind the existing user experience. Core exploration, AI tools, citations, boards, sharing, exports, and curation belong to this MVP.
