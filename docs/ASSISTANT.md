## Supabase embeddings setup

`bright-action` is deployed and verified with the configured server-only secret.
The backend defaults to this name; `EMBEDDING_FUNCTION_NAME` can override it.
Unauthenticated requests were verified to return HTTP 401.

Implemented: `gte-small`, mean pooling and normalization, 384-dimensional vectors,
private `fb_chunks` table, page-linked text offsets, resumable indexing, and bounded
semantic candidates alongside existing keyword evidence. No local model installation.
Supabase migration 002 is applied. Three original PDFs were uploaded and their downloaded
bytes checksum-verified. All 151 nonempty pages and 922 normalized embeddings are stored.
Every stored passage was checked against its exact page-text offsets.
A real semantic query retrieved three cited passages (PSI-159 pages 44, 67, 63);
their page citations and signed source download checksum were verified.
Local migration and six focused embedding/assistant tests passed.
Production backend/frontend code remains on the earlier release; no branch was pushed or deployed.

### Activate through the Supabase Dashboard

1. Create a random secret of at least 32 characters using a password manager.
2. Add it as `EMBEDDING_SECRET` in Edge Functions → Secrets.
3. Create a function named `bright-action`, paste `supabase/functions/bright-action/index.ts`, and deploy.
4. Disable legacy JWT verification for this function. The handler instead requires
   the server-only `x-embedding-secret` header and rejects missing/incorrect secrets.
   Do not deploy an unprotected replacement or put the secret in frontend settings.
5. Set the same `EMBEDDING_SECRET` in the root local `.env` and Render backend.
   `SUPABASE_URL` must also be set. No new frontend environment variables are needed.
6. Restart the local API with the root env file, preserving local DB overrides.
7. Apply `alembic upgrade head` separately to the intended database.
8. Publish the existing three-PDF bundle using `app.publish_research --upload`
   only when targeting Supabase, then run `python -m app.index_documents --remote`.
   For a local database use `python -m app.index_documents` after local PDF loading.
9. Verify a real semantic query and each returned citation/source download before enabling
   the feature in a presentation. Embedding setup alone does not deploy the backend branch.

The indexing command reads existing PDF page citations, skips completed chunks,
and commits groups of up to twelve, using at most three concurrent four-text requests. If interrupted, rerun it. Remote indexing only uses
sources whose Storage upload has been verified. Do not run with a different database
URL accidentally; `--remote` explicitly permits remote writes.

Model limits: gte-small supports English and truncates inputs at 512 tokens.
Passages are conservatively split into 400-character windows with 80-character overlap;
long/token-dense questions may still be truncated by the model.
Vector similarity is a retrieval signal, not proof that a passage supports an answer.
The initial small corpus uses exact cosine scans; no HNSW overhead yet.
If configuration, function calls, or vector queries fail, keyword evidence remains usable.
The UI describes combined semantic and keyword retrieval with fallback.

Reference: https://supabase.com/docs/guides/functions/ai-models

---

# Research assistant: first LangGraph workflow
## PDF retrieval update

The local assistant now searches extracted PDF pages alongside experiments and chart points.
Three documents are prepared by `backend/app/documents.py`: PSI-159's final report and
PSI-117's Users Group and Three Stage presentations (151 nonempty pages).
Existing source hashes and page citation IDs are reused. Original files are not modified.
The existing publisher can load this bundle after the initial research slice; it deliberately
does not overwrite investigation metadata. These three PDFs and their page citations are now published to Supabase.

Search combines Supabase gte-small passage retrieval with PostgreSQL English full-text keyword ranking.
At most three matching pages are included, each capped at 6,000 extracted characters for model context.
The citation drawer shows the full extracted page and links to the original downloadable file.
Text extraction may lose figures or table structure; these passages are not reviewed numerical datasets.
Local retrieval and the frontend production build passed. Browser-level visual review remains pending.

`POST /api/v1/assistant/ask` runs a bounded LangGraph workflow: retrieve → synthesize → validate. Request fields are `question`, up to four `experiment_ids`, and optional `chart_id`. The dashboard question panel can pass the comparison selection and optionally the displayed chart.

## Implemented

- Parameterized PostgreSQL keyword lookup over reviewed experiment fuel/run/comment fields, plus chart-title search.
- Explicit selected-record context, and selected chart endpoint/extreme samples calculated from stored values.
- Citation/source resolution before evidence is sent to generation.
- Configurable Groq/Gemini-compatible chat-completion endpoint; no SDK provider lock-in.
- At most one generation call, up to five claims, six experiment search results, and bounded chart samples.
- Validation rejects unknown citation IDs and numbers absent from the records cited by that claim.
- No-key/provider-error/unsupported-question modes return evidence or an explicit coverage limitation.
- Dashboard cited answers, evidence details, source-drawer links, and client-side request cancellation.
- Per-process limit of 20 requests per minute, maximum three concurrent requests, model timeout and 50-second workflow deadline.

The generation code supports configured Groq, Gemini, or OpenAI-compatible endpoints. Anthropic-native generation is not implemented here; selecting it returns evidence-only mode. Gemini compatibility is implemented but has not been live-tested.

## Coverage and limits

This first version searches the published PSI-159 experiment records and PSI-117 chart data. Narrative PDF chunks and semantic embeddings are not connected yet. It must not claim to search the entire NASA archive or explain unsupported combustion mechanisms.

The graph uses deterministic retrieval nodes, not autonomous model-selected tool loops. General comparison tools, full-document hybrid retrieval, streaming events, and persistent conversations remain next-stage work within this MVP.

Citation and numeric-token validation checks references and copied values, not complete semantic entailment. A number can exist in a source yet be used incorrectly in prose. The UI identifies generated interpretations and exposes the underlying evidence. No scientific certification or safety advice is supplied.

Rate limits are process-local and reset on restart. They are suitable for the current single-instance demo, not a distributed quota system. Client cancellation stops waiting in the browser; server/provider work may continue until its bounded deadline.

## Provider configuration

The configured `llama-3.3-70b-versatile` returned Groq HTTP 404 `model_not_found` during integration. The authenticated model-list endpoint reported `openai/gpt-oss-20b` as available. Use an available model via `AI_MODEL`; explicit existing `.env` or Render values override code defaults.

The local Compose API was restarted with the existing provider key, an explicit `AI_MODEL=openai/gpt-oss-20b` override, localhost CORS, and the local development database. The earlier no-key run verified evidence-only fallback. The private `.env` was not edited; future starts should preserve the model override until its explicit old model value is updated. Never put the provider key in Vite variables.

## Focused validation

- Four tests: graph no-evidence path, bounded search terms, unknown-citation rejection, and numerical values checked against the cited record rather than unrelated evidence.
- Local HTTP request returned six cited ethane records with no model key.
- Frontend build and lint passed.
- Live Groq testing with `openai/gpt-oss-20b` returned two cited pressure claims whose numeric values matched their retrieved records. Code defaults and deployment examples now use this available model. Existing explicit environment values still need updating.

Next: store narrative chunks, add hybrid retrieval, and extend the graph to a wider evidence base without losing source locators.
