# Firebusters deployment architecture

**Status:** Target architecture accepted; temporary deployment override active

**Target decision:** Use Koyeb for the backend.

**Temporary decision:** Use Render for the deadline deployment while Koyeb account approval is pending.

This file is the authoritative record of the deployment decision. The application is currently deployed to Render for the hackathon deadline. Migrate the same Docker service to Koyeb after account approval; Supabase, R2 and Vercel do not change.

## Architecture

```text
Vercel
React/Vite frontend
        │
        ▼
Koyeb
FastAPI agent and analytics API
        │
        ├── Supabase PostgreSQL + pgvector
        ├── Cloudflare R2 object storage
        ├── Supabase Edge Functions + gte-small embeddings
        └── Gemini API for generation and tool calling

Local machine
Heavy ingestion and scientific preprocessing
```

| Component | Platform | Responsibility |
| --- | --- | --- |
| Frontend | Vercel | React application, CDN, HTTPS and preview deployments |
| Backend | Koyeb Free | Dockerized FastAPI API |
| Database | Supabase Free | PostgreSQL, pgvector and optional authentication |
| Object storage | Cloudflare R2 | PDFs, selected videos, Parquet, grids, images and exports |
| Embeddings | Supabase Edge Functions + `gte-small` | 384-dimensional semantic-search vectors |
| Generation | Gemini | Agent reasoning, synthesis and tool calling |
| Heavy ingestion | Local machine | Extraction, conversion, preprocessing and bulk uploads |
| CI/CD | Platform Git integration; GitHub Actions later | Builds, tests and automatic deployments |

## Why Koyeb instead of Render

Render is easy to configure, but the free web service's longer cold start is risky during a live demonstration. Its small instance and lack of a free background worker also do not improve this architecture.

Koyeb is the selected hackathon backend because it supports:

- Git-driven Docker deployments
- A free web service
- Scale-to-zero with a shorter documented wake-up path
- Monorepo work directories
- Runtime secrets and environment variables
- HTTP health checks

Deploy the service in Frankfurt when the free instance is available there. Keep Supabase in the closest practical region. Koyeb may require payment-card verification even when the selected instance is free.

Google Cloud Run remains the stronger fallback when a billing account is acceptable. It offers more configurable memory and Cloud Run Jobs, but has more setup and accidental-billing risk.

### Temporary Render deployment

Koyeb account approval was not available before the deployment deadline. Render is therefore the active short-term backend because it can deploy the existing Dockerfile directly from GitHub without introducing a new billing or IAM setup.

This does not change the workload boundary:

- Heavy ingestion stays local.
- PostgreSQL and vectors stay in Supabase.
- Large assets stay in R2.
- Render serves only the online API.
- Warm the free Render service immediately before judging because it sleeps after inactivity.

## Data placement

### Supabase PostgreSQL

Store compact, queryable records:

- Investigations and experiments
- Normalized experimental conditions
- Document chunks and citations
- 384-dimensional embeddings
- File manifests
- Derived statistics

Do not store large PDFs, videos, image sequences, spatial grids or Parquet files in PostgreSQL.

Use Supabase's shared session pooler on port `5432` for the persistent Koyeb service. The URL must use `postgresql+asyncpg://` and `ssl=require`.

### Cloudflare R2

Use a private R2 bucket for:

```text
derived/
├── psi115/*.parquet
├── psi115/heatmap-tiles/*
├── psi117/*.parquet
├── psi159/selected-video/*
├── thumbnails/*
└── exports/*
```

Do not upload the complete 1.90 TB PSI-159 archive. Upload only selected raw assets and useful derived products. The backend should issue short-lived presigned URLs; R2 credentials must never reach the browser.

## Search and AI strategy

- Generate semantic-search embeddings with the Supabase Edge `gte-small` model.
- Embed report chunks, guide sections, investigation descriptions and safety case studies.
- Query structured experiment records using SQL; do not embed every numerical row.
- Use Gemini as the default generation provider while retaining the provider abstraction for OpenAI and Anthropic.
- Cache common guided-story responses and return structured charts/data when the LLM is unavailable.
- Add rate limits and short provider timeouts before the public demo.

## Workload boundary

The free Koyeb instance should serve requests, not process the source archive.

Run locally:

- PDF and Office document extraction
- Grid and spreadsheet conversion
- Large Polars/PyArrow transformations
- Thumbnail and video-frame generation
- Bulk embedding preparation
- Bulk uploads to Supabase and R2

Run on Koyeb:

- PostgreSQL queries
- Lightweight analysis
- Retrieval and agent orchestration
- Gemini calls
- Streaming API responses
- Presigned R2 URL generation

Redis and Celery are not part of the MVP. Reconsider a queue only when ingestion must survive an API request or multiple users can launch durable jobs concurrently.

## Constraints and follow-up work

The current backend image still includes ingestion libraries such as PyArrow, Polars and document parsers. Before the final deployment, split online runtime dependencies from local ingestion dependencies so the 512 MB service has more memory headroom and faster builds.

Required repository work:

1. Keep production environment configuration synchronized with `.env.example`.
2. Split runtime and ingestion dependency groups/images.
3. Add Supabase schema migrations.
4. Add Koyeb secrets and deploy the API.
5. Configure Vercel and R2 after the Koyeb public domain is known.
