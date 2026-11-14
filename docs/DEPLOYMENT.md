# Deployment

Firebusters uses four managed services so the hackathon deployment stays small and inexpensive:

| Layer | Platform | Purpose |
| --- | --- | --- |
| Web app | Vercel | React/Vite static deployment and CDN |
| API | Koyeb | Dockerized FastAPI service |
| Database | Supabase | PostgreSQL and pgvector |
| Object storage | Cloudflare R2 | Private NASA source files and generated artifacts |

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

## 2. Koyeb API

1. Push the repository to GitHub.
2. In Koyeb, create a Web Service and select GitHub as the deployment method.
3. Select the `SobanSheikh/firebusters` repository and its default branch.
4. Select the Dockerfile builder.
5. Set the Work directory to `backend`; the Dockerfile path is then `Dockerfile`.
6. Select the free instance in Frankfurt when available.
7. Expose port `8000` as HTTP and route `/` to it.
8. Configure the HTTP health check path as `/api/v1/health/live`.
9. Add the environment variables listed below. Store credentials as Koyeb Secrets and reference them from environment variables.
10. Initially set `CORS_ORIGINS` to `http://localhost:5173`.
11. Deploy and verify `https://YOUR_KOYEB_DOMAIN/api/v1/health`.

Koyeb automatically provides `PORT`; the backend Dockerfile reads it and defaults to `8000`. The liveness endpoint does not depend on the database. The full health endpoint does, which makes it useful for diagnostics without causing a transient database issue to restart the API.

The free service can scale to zero after inactivity, so warm it shortly before judging. Do not put long dataset ingestion inside a web request. Run ingestion locally for the hackathon and upload normalized outputs to Supabase/R2.

## 3. Vercel frontend

1. Import the same GitHub repository into Vercel.
2. Set the project Root Directory to `frontend`.
3. Vercel reads `frontend/vercel.json` and installs with Bun.
4. Add this production environment variable:

```text
VITE_API_BASE_URL=https://YOUR_KOYEB_DOMAIN/api/v1
```

5. Deploy the frontend.
6. Replace Koyeb's `CORS_ORIGINS` with the exact Vercel origin, for example `https://firebusters.vercel.app`. Multiple origins are comma-separated.
7. Redeploy the Koyeb service and test the frontend.

Vite variables are public browser configuration. Never create a `VITE_SUPABASE_SECRET_KEY` or expose an R2 secret.

## 4. Cloudflare R2

R2 is optional until upload/ingestion features are implemented.

1. Create a private bucket named `flamelens-assets`.
2. Create an Object Read & Write API token scoped only to that bucket.
3. Add its endpoint, access key ID, and secret to Koyeb.
4. Keep the bucket private. The backend will issue short-lived presigned URLs for browser upload/download.
5. Copy `infra/r2-cors.example.json`, replace `YOUR_VERCEL_DOMAIN`, and apply it as the bucket CORS policy before enabling browser uploads.

Do not upload the full raw PSI archive to Git or Supabase. Put raw files in R2, normalized metadata/chunks/measurements in PostgreSQL, and vectors in pgvector.

## Production environment map

### Koyeb

```text
ENVIRONMENT=production
DATABASE_URL=...
CORS_ORIGINS=https://YOUR_VERCEL_DOMAIN
SUPABASE_URL=...
SUPABASE_PUBLISHABLE_KEY=...
SUPABASE_SECRET_KEY=...
AI_PROVIDER=gemini
GEMINI_API_KEY=...
R2_ENDPOINT=...
R2_BUCKET=flamelens-assets
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_PUBLIC_BASE_URL=
```

### Vercel

```text
VITE_API_BASE_URL=https://YOUR_KOYEB_DOMAIN/api/v1
```

Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` only when browser-side Supabase Auth is added.
