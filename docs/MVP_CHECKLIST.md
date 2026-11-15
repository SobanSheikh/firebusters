# Firebusters judged-MVP checklist

Checked items have implementation or validation evidence. Unchecked items remain open; this checklist does not imply production deployment. Scope: [PRODUCT_PLAN.md](PRODUCT_PLAN.md). Working slice: [RESEARCH_WORKFLOW.md](RESEARCH_WORKFLOW.md).

## 1. Local evidence foundation

- [x] Inventory original collection with stable source IDs, checksums, and duplicate aliases.
- [x] Extract PDF pages and CSV records with source locators.
- [x] Prepare text chunks while preserving page citations.
- [x] Parse PSI-115 grid, particle-distribution, and diameter formats separately.
- [x] Flag extra values and nonfinite numbers rather than silently repairing them.
- [x] Normalize 179 PSI-159 experiment records and 205 PSI-117 experimental chart points.
- [x] Preserve unknown values, normalized units, and experimental/simulation distinctions.
- [ ] Refresh the full inventory and ingestion bundle to include PSI-68.
- [ ] Add reviewed adapters for remaining spreadsheets, metadata archives, and DOCX sources.
- [ ] Resolve empty/scanned PDF pages and the unreadable FLEX-1248 file.
- [ ] Confirm PSI-115 coordinates, ordering, units, and node mappings; investigate nine flagged files.
- [ ] Publish reviewed coverage and extraction-quality metadata for all current investigations.

## 2. Database and publication

- [x] Create initial investigations, sources, citations, experiments, and charts migration.
- [x] Apply migration to the local development database.
- [x] Load the selected slice locally and verify repeat loading does not duplicate records.
- [x] Implement private-source upload/checksum verification and transactional upsert path.
- [x] Implement stable source routes and fresh signed-URL resolution.
- [x] Review migration and publication changes before applying them to Supabase.
- [x] Apply the approved shared migration and upload the selected sources (2 files, 179 experiments, 384 citations, 205 chart points).
- [x] Verify cloud download checksums and access restrictions; regenerate signed links twice per source. Expiry-boundary testing was not performed.
- [ ] Add schema support for chunks/embeddings, richer measurements, derivations, boards, and review history.

## 3. Explorer and interactive dashboard

- [x] Build Mission Control layout with real collection counts.
- [x] Add fuel filtering and paginated experiment records.
- [x] Compare up to four experiments with source links.
- [x] Plot the experimental PSI-117 series with a cited point inspector.
- [x] Add the source drawer and original-file downloads.
- [x] Validate local API filtering, pagination, citation locators, and source checksums.
- [ ] Complete focused browser review: filtering, comparison, point inspector, keyboard drawer behavior, downloads, and narrow-screen layout.
- [x] Split chart code from the initial application bundle and check the production build (main JS 734 KB → 363 KB; chart chunk 372 KB).
- [x] Implement native modal source drawer with Escape dismissal, focus restoration, and background scroll locking; build/lint passed.
- [ ] Add full investigation detail views and filters for the reviewed catalog.
- [ ] Add validated Gravity Lens heatmaps and compatible difference views.
- [ ] Add linked chart selections, zoom/reset, and additional reviewed numerical series.
- [x] Add a three-minute presentation route, transcript-aligned challenge outcomes, reviewed-slice coverage boundary, and investigation cards; production build passed.

## 4. AI research assistant

- [x] Store 922 page-linked passages and normalized gte-small embeddings (384 dimensions) across 151 PDF pages.
- [x] Implement bounded keyword/structured lookup over published experiment and chart records.
- [x] Add local PDF-page keyword retrieval and PDF text in the citation drawer: three PDFs, 151 nonempty pages; focused retrieval and frontend build passed.
- [x] Publish three PDFs and 151 page citations to Supabase; original downloads checksum-verified.
- [x] Deploy Supabase `bright-action` and configure server-only `EMBEDDING_SECRET`; anonymous requests return 401.
- [x] Implement gte-small client, resumable indexing, private vector schema, and combined semantic/keyword retrieval with keyword fallback.
- [x] Generate all 922 embeddings; verify exact offsets for every passage and a real semantic query with three page citations and a signed source download.
- [ ] Deploy dev-branch backend/frontend changes after presentation readiness review.
- [x] Implement LangGraph retrieval → synthesis → validation with selected experiment/chart context.
- [ ] Extend to general comparison tools and model-selected chart/tool workflows.
- [x] Connect configurable Groq generation; live cited answer verified with `openai/gpt-oss-20b` after the old model returned 404.
- [x] Validate citation membership and numerical tokens against cited records; semantic entailment still requires source inspection.
- [x] Add client cancellation, process-local request/concurrency limits, and provider/workflow timeouts.
- [x] Bound each question to one retrieval pass, at most one embedding call, one generation call, 12 evidence records, and one relevant reviewed chart.
- [ ] Add streamed workflow progress and response events.
- [x] Provide evidence-only fallback when generation is unavailable and a deterministic cited-chart fallback when generated claims fail validation.
- [x] Verify a real numerical question end-to-end: four cited claims, one reviewed chart, 12 bounded evidence records, one generation, and a roughly three-second local response.

## 5. Stories, relationships, and impact

- [ ] Build cited Cool Flames, Gravity and Smoke, and Spacecraft Fire Lessons routes.
- [ ] Add documented investigation/topic/facility relationships and an accessible list alternative.
- [ ] Add source-backed timelines and impact cards.
- [ ] Verify that curated stories remain usable without live generation.

## 6. Boards, exports, and curation

- [ ] Support guest boards with saved charts, experiments, answers, and notes.
- [ ] Add optional authentication and owner-only cloud persistence.
- [ ] Implement explicit share links and revocation.
- [x] Export selected experiment rows as a CSV with original values and stable citation IDs; protect formula-leading cells.
- [ ] Export a research brief/PDF, chart image, and full citation manifest.
- [ ] Add curator roles, metadata corrections, quality review, and revision history.
- [ ] Verify ownership and sharing boundaries with focused permission tests.

## 7. Presentation release

- [ ] Complete the primary journey: explore → compare → ask → cite → save/export.
- [x] Translate the official video transcript into the visible three-outcome judge path and add supported, numerical, modeling, and unsupported-lunar suggested questions.
- [x] Audit the official transcript and NASA combustion overview against the delivered assistant: investigation relevance, model-ready extraction, control/equipment relevance, gravity and atmosphere boundaries, and reviewed-slice disclosure are covered.
- [ ] Review and merge the finished dev release to main when authorized.
- [ ] Verify Vercel-to-Render CORS, production data, citations, and critical workflows.
- [ ] Rehearse a five-minute and a three-minute judge walkthrough.
- [ ] Prepare a clearly identified backup recording and warm the API before judging.

## Testing rule

Run checks proportional to the change: build/lint for UI changes; citation and parser checks for data changes; migration/permissions checks for schema or access changes. Reuse completed evidence. Do not rerun broad suites without a relevant change or failure. Browser review remains a separate unchecked item until actually performed.

## Next execution order

1. Complete the focused browser review, especially narrow-screen chart/source behavior and the judge route.
2. Rehearse the three-minute judge journey and fix only presentation-blocking issues.
3. Deploy the reviewed dev release, then verify Vercel-to-Render CORS, citations, rate-limit behavior, and source downloads.
4. Expand chart coverage, stories, boards/exports, and curation after the presentation-critical path is stable.

The later product phase expands datasets and infrastructure; the core features above belong to the judged MVP.
