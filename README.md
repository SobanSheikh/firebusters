# Firebusters / FlameLens

Evidence-first exploration of NASA Physical Sciences Informatics combustion investigations for the NASA Space Apps **Flame in Freefall** challenge.

## Stack

The project mirrors the core go4gr8 stack:

- React 19, TypeScript, Vite/SWC and Tailwind CSS 4
- TanStack Query, Axios, Zustand and Recharts
- FastAPI, Pydantic, async SQLAlchemy and Alembic
- PostgreSQL 16 with pgvector
- LangGraph/LangChain with OpenAI and Anthropic provider support
- Docker Compose and `uv`

## Run locally

```bash
cp .env.example .env
docker compose up --build -d

cd frontend
bun install
bun run dev
```

Then open:

- Dashboard: http://localhost:5173
- API docs: http://localhost:8001/docs
- Health: http://localhost:8001/api/v1/health

NASA source files belong in `data/raw/`. Keep large source files out of Git. Normalized JSON or Parquet output belongs in `data/processed/`.

Dataset ingestion runs as an explicit backend command. Redis and Celery are intentionally deferred until the product needs durable background jobs or concurrent uploads.

The backend and PostgreSQL are containerized. The Vite frontend runs directly with Bun during development for faster startup and dependency installation. Its Dockerfile remains available for production builds.

## Deploy

The presentation deployment uses Vercel, Render, Supabase PostgreSQL/Storage, and only the currently downloaded NASA files. Koyeb and Cloudflare R2 remain post-demo options. See the [product plan](docs/PRODUCT_PLAN.md), [architecture decision](docs/ARCHITECTURE.md), and [deployment guide](docs/DEPLOYMENT.md).
