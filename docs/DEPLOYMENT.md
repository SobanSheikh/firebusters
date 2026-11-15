# Deployment

Firebusters uses four managed services so the hackathon deployment stays small and inexpensive:

| Layer | Platform | Purpose |
| --- | --- | --- |
| Web app | Vercel | React/Vite static deployment and CDN |
| API | Render (temporary) | Dockerized FastAPI service |
| Database | Supabase | PostgreSQL and pgvector |
| Object storage | Supabase Storage (MVP) | Private NASA source files and generated artifacts |

Redis and Celery are intentionally deferred. Add a worker only when ingestion must continue after an API request ends or multiple users can start jobs concurrently.

## 1. Supabase

The database URL must use the session pooler, the `asyncpg` scheme, and TLS:

```text
postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@POOLER_HOST:5432/postgres?ssl=require
```

Enable pgvector once in the SQL editor:

```sql
create extension if not exists vector with schema extensions;
```

Keep the database password and secret API key on the backend only.

The architecture decision and rationale are recorded in [ARCHITECTURE.md](ARCHITECTURE.md).

## 2. Render API

1. Push the repository to GitHub.
2. In Render, select **New → Blueprint**.
3. Connect the `SobanSheikh/firebusters` repository.
4. Render reads `render.yaml` and creates the `firebusters-api` free web service in Singapore.
5. Enter every value marked `sync: false`. Copy values from the local `.env`; never commit them.
6. Keep `CORS_ORIGINS=http://localhost:5173` until the Vercel production URL exists.
7. Apply the Blueprint and follow the build logs.
8. Verify `https://YOUR_RENDER_HOST/api/v1/health/live` and then `/api/v1/health`.

Render provides `PORT`; the backend Dockerfile reads it and defaults to `8000` locally. The liveness endpoint does not depend on the database. The full health endpoint does, which makes it useful for diagnostics without causing a transient database issue to restart the API.

The free service sleeps after 15 minutes without inbound traffic and can take approximately one minute to wake. Open the health endpoint two to three minutes before judging. Do not put ingestion inside a web request; run it locally and upload normalized outputs to Supabase Storage/PostgreSQL.

## 3. Vercel frontend

1. Import the same GitHub repository into Vercel.
2. Set the project Root Directory to `frontend`.
3. Vercel reads `frontend/vercel.json` and installs with Bun.
4. Add this production environment variable:

```text
VITE_API_BASE_URL=https://YOUR_RENDER_HOST/api/v1
```

5. Deploy the frontend.
6. Replace Render's `CORS_ORIGINS` with the exact Vercel origin, for example `https://firebusters.vercel.app`. Multiple origins are comma-separated.
7. Save the Render environment change and test the frontend.

Vite variables are public browser configuration. Never create a `VITE_SUPABASE_SECRET_KEY` or expose an R2 secret.

## 4. Supabase Storage

The presentation MVP uses a private bucket named `firebusters-assets`.

- Original files and presentation artifacts go into Storage.
- Metadata, chunks, citations, vectors and compact statistics go into PostgreSQL.
- The backend uses the secret key to create short-lived signed URLs.
- Never expose `SUPABASE_SECRET_KEY` in a `VITE_*` variable.

The ingestion pipeline runs locally and uploads only the current 141-file dataset. See [PRODUCT_PLAN.md](PRODUCT_PLAN.md) for the tiered processing scope.

## 5. Cloudflare R2 (later)

R2 is deferred until larger NASA datasets, videos, Parquet or grids make it necessary.

1. Create a private bucket named `flamelens-assets`.
2. Create an Object Read & Write API token scoped only to that bucket.
3. Add its endpoint, access key ID, and secret to Render.
4. Keep the bucket private. The backend will issue short-lived presigned URLs for browser upload/download.
5. Copy `infra/r2-cors.example.json`, replace `YOUR_VERCEL_DOMAIN`, and apply it as the bucket CORS policy before enabling browser uploads.

Do not upload the full raw PSI archive to Git or Supabase. Put raw files in R2, normalized metadata/chunks/measurements in PostgreSQL, and vectors in pgvector.

## Production environment map

### Render

```text
ENVIRONMENT=production
DATABASE_URL=...
CORS_ORIGINS=https://YOUR_VERCEL_DOMAIN
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SECRET_KEY=...
SUPABASE_STORAGE_BUCKET=firebusters-assets
AI_PROVIDER=gemini
```

Add `GEMINI_API_KEY` when assisted synthesis is implemented. Add the R2 variables only when the extensive storage plan is activated.

### Vercel

```text
VITE_API_BASE_URL=https://YOUR_RENDER_HOST/api/v1
```

Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` only when browser-side Supabase Auth is added.

## Post-demo migration

Koyeb remains the target backend after account approval. Migration requires deploying the same `backend/Dockerfile`, copying the environment variables, changing `VITE_API_BASE_URL`, and updating `CORS_ORIGINS`. No database or object migration is required.
