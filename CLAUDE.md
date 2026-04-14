# CLAUDE.md

## Project Overview

**AppArt Agent** is an AI-powered apartment purchasing decision platform for the French real estate market. It's a monorepo with a FastAPI backend, Next.js frontend, and GCP-based infrastructure.

## Architecture

```text
/
├── backend/          # FastAPI API (Python 3.10)
├── frontend/         # Next.js 14 app (React 18, TypeScript)
├── infra/            # Terraform IaC for GCP
├── docs/             # MkDocs documentation site
├── scripts/          # GCP bootstrap scripts
├── data/             # DVF dataset (5M+ French property transactions)
└── docker-compose.yml
```

### Backend (`backend/`)

- **Framework**: FastAPI with Uvicorn (ASGI)
- **ORM**: SQLAlchemy 2.0 with Alembic migrations
- **AI**: Google Gemini (gemini-2.5-flash for text, gemini-2.5-flash-image for images) via `google-genai` SDK. Supports Vertex AI (production) or REST API key (development).
- **Auth**: Better Auth (session-based, managed by frontend) with legacy JWT fallback
- **Storage**: MinIO (local dev) / Google Cloud Storage (production) -- abstracted in `app/services/storage.py`
- **Caching**: Redis via fault-tolerant `app/core/cache.py` -- Redis down = cache miss, never an error. Key cached endpoints: `/api/properties/dvf-stats` (1h TTL), `/api/properties/{id}/price-analysis` (30min TTL), `/api/properties/{id}/price-analysis/full` (30min TTL)
- **Entry point**: `backend/app/main.py`
- **Config**: `backend/app/core/config.py` (Pydantic settings from env vars)
- **Email**: Resend SDK for transactional emails (password reset, feedback). Best-effort delivery via `app/services/email.py`
- **API routes**: `backend/app/api/` (users, properties, documents, photos, analysis, webhooks, feedback)
- **Services**: `backend/app/services/` (ai/, documents/, storage, dvf_service, price_analysis, email)
- **Models**: `backend/app/models/` (user, property, document, photo, analysis, dvf)

### Frontend (`frontend/`)

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.3 with semantic design tokens
- **UI Components**: Shared component library (`frontend/src/components/ui/`)
- **State**: TanStack React Query v5
- **Auth**: Better Auth 1.4 with Google OAuth support
- **i18n**: next-intl (locales: `fr`, `en`, default: `fr`)
- **Icons**: Lucide React
- **Analytics**: PostHog (`posthog-js`) with reverse proxy via Next.js rewrites (`/ingest/*`). Gated on GDPR cookie consent — PostHog only initializes after user accepts analytics cookies
- **PWA**: `@ducanh2912/next-pwa` (installable on mobile, disabled in dev)
- **API client**: Axios (`frontend/src/lib/api.ts`) hitting `NEXT_PUBLIC_API_URL`
- **Pages**: `frontend/src/app/[locale]/` (dashboard, properties, documents, photos, redesign-studio, price-analyst, settings, legal/privacy, legal/terms, auth/forgot-password, auth/reset-password)
- **Package manager**: pnpm
- **Address autocomplete**: Property creation uses api-adresse.data.gouv.fr (French government geocoding API) directly from the frontend for instant address suggestions — no backend call needed during typing

#### Design System

The frontend uses a semantic color token system defined in `tailwind.config.js`. **Never use raw Tailwind color names** (e.g., `blue-600`, `red-500`). Always use the semantic tokens:

| Token | Palette | Usage |
|-------|---------|-------|
| `primary-*` | Blue (#2563eb) | Main CTAs, links, active states, focus rings |
| `accent-*` | Indigo (#4f46e5) | Secondary features: studio, photos, documents, AI |
| `success-*` | Emerald (#10b981) | Positive states, confirmations |
| `warning-*` | Amber (#f59e0b) | Warnings, outliers, caution states |
| `danger-*` | Red (#dc2626) | Errors, destructive actions, high risk |

Shared UI components live in `frontend/src/components/ui/`:

| Component | Purpose |
|-----------|---------|
| `Button` | 6 variants (primary, secondary, accent, ghost, danger, link), 2 sizes |
| `Badge` | 6 variants (success, warning, danger, info, accent, neutral) |
| `Card` | Consistent card wrapper with padding options |
| `SectionHeader` | Section title with icon and optional action |
| `StatCard` | Dashboard stat card with icon |
| `Footer` | Site footer with copyright, tagline, links to legal pages |
| `CookieConsent` | GDPR cookie consent banner (accept/reject/manage). Exports `getAnalyticsConsent()` |
| `FeedbackButton` | Floating feedback button + modal (bug report, feature request, general feedback) |
| `FeedbackModal` | Feedback form with type selector, message, email, screenshot upload (5MB max) |

Utility CSS classes are defined in `globals.css` (`btn-primary`, `btn-secondary`, `badge-success`, etc.).

#### PWA (Progressive Web App)

The app is installable on mobile devices via `@ducanh2912/next-pwa`. Configuration is in `next.config.js`:

- **Disabled in development** (`disable: process.env.NODE_ENV === 'development'`)
- Service worker and Workbox files (`sw.js`, `workbox-*.js`) are generated during `pnpm build` into `public/` and gitignored
- Manifest at `frontend/public/manifest.json`, icons in `frontend/public/icons/`
- PWA metadata (viewport, manifest link, apple-web-app) in `frontend/src/app/[locale]/layout.tsx`
- Stale service workers are auto-unregistered in development via `Providers.tsx`

**Important**: Never commit generated `sw.js` or `workbox-*.js` files. They are build artifacts.

## Development Setup

### Prerequisites

- Docker and Docker Compose
- [`go-task`](https://taskfile.dev) CLI
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+ with pnpm 10+
- Copy `.env.example` to `.env` and fill in required values

### Running the Dev Environment

Everything runs via Docker Compose. Use [`go-task`](https://taskfile.dev):

```bash
task start              # Start all services (MinIO storage)
task start-gcs          # Start with Google Cloud Storage instead
task stop               # Stop all services
task logs [-- service]  # Follow logs (backend, frontend, db, redis, minio)
task restart -- <svc>   # Restart a specific service
task rebuild [-- svc]   # Rebuild and restart
task status             # Show service status
task shell [-- svc]     # Shell into container (default: backend)
```

### Services (docker-compose)

| Service    | URL                        | Notes                          |
|------------|----------------------------|--------------------------------|
| Backend    | http://localhost:8000      | API docs at /docs              |
| Frontend   | http://localhost:3000      | Next.js with HMR              |
| PostgreSQL | localhost:5432             | postgres:15-alpine             |
| Redis      | localhost:6379             | redis:7-alpine                 |
| MinIO      | http://localhost:9000      | Console at http://localhost:9001 |

Database migrations run automatically via the `migrations` service on `docker-compose up`.

**Storage backend**: `docker-compose.yml` defaults to MinIO (`STORAGE_BACKEND=minio`) but respects the `.env` override. If `.env` has `STORAGE_BACKEND=gcs`, the backend uses Google Cloud Storage. After switching backends, flush the Redis presigned URL cache: `docker compose exec redis redis-cli EVAL "local k=redis.call('KEYS','presigned_url:*'); if #k>0 then return redis.call('DEL',unpack(k)) else return 0 end" 0`

### Running Tests

Tests run on the host using uv:

```bash
cd backend
uv run pytest                    # Run all tests
uv run pytest --cov              # With coverage
uv run pytest tests/test_dvf_service.py  # Specific test file
```

Testing stack: pytest + pytest-asyncio + pytest-cov.

### Load Testing (Locust)

Locust is installed as a root-level dev dependency. Run from the project root:

```bash
# Backend API load test (Web UI at http://localhost:8089)
uv run python -m locust -f loadtest/locustfile.py --host https://api.appartagent.com

# Frontend SSR load test (run separately with different host)
uv run python -m locust -f loadtest/locustfile.py --host https://appartagent.com FrontendUser

# Headless mode for CI
uv run python -m locust -f loadtest/locustfile.py --host https://api.appartagent.com --headless -u 50 -r 5 --run-time 2m AppArtUser
```

Two user classes: `AppArtUser` (backend API) and `FrontendUser` (SSR pages). Environment variables: `LOCUST_AUTH_TOKEN` (Better Auth session cookie), `LOCUST_PROPERTY_ID` (default: 1).

## Dependency Management

### Python (uv only -- never use pip or bare `python`)

**Always use `uv run` to execute Python scripts and commands.** Never invoke `python` directly -- `uv run` ensures the correct virtualenv and dependencies are used.

```bash
uv add <package>        # Add a dependency
uv remove <package>     # Remove a dependency
uv sync                 # Sync from lock file
uv run <command>        # Run a command in the venv (never bare `python`)
```

Lock file: `uv.lock` (root level). Backend deps defined in `backend/pyproject.toml`.

### Frontend (pnpm)

```bash
cd frontend
pnpm install            # Install deps
pnpm dev                # Dev server (but prefer docker-compose)
pnpm build              # Production build
pnpm lint               # ESLint
```

Lock file: `frontend/pnpm-lock.yaml`.

## Code Quality & Linting

### Pre-commit Hooks

Pre-commit is configured (`.pre-commit-config.yaml`) and runs automatically on commit:

- **Python**: ruff (lint + format), mypy (type check), bandit (security)
- **Frontend**: ESLint, TypeScript type check (`tsc --noEmit`)
- **Markdown**: markdownlint-cli2
- **General**: trailing whitespace, EOF fixer, YAML/JSON/TOML checks, large file detection
- **Secrets**: gitleaks
- **Commits**: conventional-pre-commit (enforces conventional commit format)

### Manual Linting

```bash
uv run ruff check backend/     # Python lint
uv run ruff format backend/    # Python format
cd frontend && pnpm lint       # Frontend lint
pre-commit run --all-files     # Run all hooks
```

### Ruff Config

- Line length: 100
- Target: Python 3.10
- Ignores: E501 (line length), E711/E712 (SQLAlchemy comparison patterns)

## Git Conventions

### Commits

**Conventional commits are enforced by pre-commit.** Allowed types:

`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

Examples:

```text
feat: add tantieme detection to document analysis
fix: bulk upload status lost on page reload
docs: update DVF import guide
```

### Branching

- `main` -- production, deployed to GCP Cloud Run
- `develop` -- integration branch, PR target for features
- Never push directly to `main`

### Pull Requests

- Target `develop` for feature work
- Target `main` only for releases/hotfixes

## Environment Variables

Key variables (see `.env.example` for full list):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | GCP region (default: us-central1) |
| `GEMINI_USE_VERTEXAI` | Use Vertex AI (production) vs REST API key (dev) |
| `GOOGLE_CLOUD_API_KEY` | Gemini REST API key (only needed when `GEMINI_USE_VERTEXAI=false`) |
| `GEMINI_LLM_MODEL` | Text analysis model (default: gemini-2.5-flash) |
| `GEMINI_IMAGE_MODEL` | Image generation model (default: gemini-2.5-flash-image) |
| `BETTER_AUTH_SECRET` | Auth secret (32+ chars) |
| `SECRET_KEY` | Backend secret key |
| `DATABASE_URL` | PostgreSQL connection string |
| `STORAGE_BACKEND` | `minio` (dev) or `gcs` (prod) |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO credentials |
| `GCS_DOCUMENTS_BUCKET` / `GCS_PHOTOS_BUCKET` | GCS bucket names |
| `NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN` | PostHog project token (optional, leave empty to disable) |
| `NEXT_PUBLIC_POSTHOG_HOST` | PostHog host (default: `https://eu.i.posthog.com`) |
| `RESEND_API_KEY` | Resend API key for transactional emails: password reset, feedback (optional) |
| `FEEDBACK_EMAIL` | Destination email for feedback submissions |
| `EMAIL_FROM` | Sender address for outgoing emails |
| `INTERNAL_API_URL` | Backend URL for server-side calls inside Docker (`http://backend:8000`). Used by Better Auth's password reset hook. Not needed outside Docker. |
| `LOGFIRE_TOKEN` | Observability (optional) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth (optional) |

**Never commit `.env` files.** They are in `.gitignore`.

## Infrastructure & Deployment

### GCP Architecture (Production)

- **Compute**: Google Cloud Run (serverless containers)
- **Database**: Cloud SQL (PostgreSQL)
- **Storage**: Google Cloud Storage (documents + photos buckets)
- **AI**: Vertex AI (managed Gemini models)
- **Registry**: Google Artifact Registry (Docker images)
- **IaC**: Terraform (`infra/terraform/`)
- **Network security**: Backend Cloud Run uses `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` — only reachable via the load balancer (`api.appartagent.com`) or from within the VPC. Direct `*.run.app` URLs are not publicly accessible.

### Terraform

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

Managed resources: Cloud Run services, Cloud Run Jobs (DB migrations + DVF import), GCS buckets, Cloud SQL, Memorystore Redis, IAM, Secret Manager.

Key variable: `backend_max_concurrency` (default: 20) controls per-instance request concurrency on the backend Cloud Run service. Lower than the Cloud Run default of 80 to trigger autoscaling sooner for DB-heavy endpoints.

### GCP Bootstrap

First-time GCP setup:

```bash
./scripts/gcp-bootstrap.sh  # Enables APIs, creates resources, sets up Terraform
```

### Docker Images

- **Backend**: Multi-stage build (`backend/Dockerfile`) -- builder, dev, production stages. Uses uv for fast installs. Production runs as non-root `appuser`.
- **Frontend**: `frontend/Dockerfile.pnpm` for production (pnpm-optimized). `frontend/Dockerfile` for dev.

### CI/CD (GitHub Actions)

`.github/workflows/deploy.yml`:

1. **Build & Test**: Python (uv + ruff + pytest), Node.js (pnpm + eslint + tsc)
2. **Push images**: To Artifact Registry (on main branch only)
3. **Migrate DB**: Run Alembic migrations + update DVF import job image
4. **Deploy**: Backend + Frontend to Cloud Run

`.github/workflows/dvf-import.yml`: Manually triggered workflow that executes the `dvf-import` Cloud Run Job (downloads + imports full DVF dataset into Cloud SQL).

`.github/workflows/docs.yml`: Builds and deploys MkDocs to GitHub Pages.

## Trust & Safety

- **Legal pages**: Privacy policy (`/legal/privacy`) and Terms of Service (`/legal/terms`), fully translated FR/EN with in-page language switcher and back button
- **GDPR cookie consent**: Banner with accept/reject/manage. PostHog analytics only initializes after user consents. Consent stored in `cookie_consent` cookie, communicated via `CustomEvent('cookie-consent-change')`
- **Error pages**: Custom 404 (root-level `not-found.tsx`) and 500 error boundary (`error.tsx` with i18n)
- **Feedback system**: Floating button + modal → `POST /api/feedback` (public, rate-limited 5/min/IP, XSS-safe) → email via Resend. Supports bug reports, feature requests, general feedback with optional screenshot
- **Footer**: Shared footer on all pages with copyright, tagline, legal page links

## Account Management

- **Settings page** (`/settings`): Protected page with profile editing (name via Better Auth `updateUser`), password change (via Better Auth `changePassword`), FR/EN language toggle, and danger zone for account deletion
- **Password reset flow**: "Forgot password?" link on login → `/auth/forgot-password` (email form) → Better Auth's `/request-password-reset` endpoint → `sendResetPassword` hook calls `POST /api/users/send-reset-email` → Resend delivers branded email with reset link → `/auth/reset-password` (new password form) → Better Auth's `/reset-password` endpoint
- **Account deletion**: `DELETE /api/users/me` — cascading cleanup: storage files (photos, documents, best-effort), Better Auth data (sessions, accounts, verifications, ba_user), then user record (SQLAlchemy cascades handle properties, documents). Requires typing DELETE/SUPPRIMER to confirm
- **Header**: User name with chevron dropdown → Settings and Logout. Language auto-detected from browser `Accept-Language` (next-intl `localeDetection: true`), changeable in Settings

## Key Domain Concepts

- **DVF** (Demandes de Valeurs Foncieres): French government open dataset of 20M+ geolocalized property transactions. Schema: `dvf_sales` (~4.8M rows, one per transaction) + `dvf_sale_lots` (~13.5M rows, one per lot). Source: [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/). Download with `uv run download-dvf <url>` (extracts into `data/dvf/`). Import with `uv run import-dvf` (polars + COPY FROM STDIN, ~55s locally; ~25 min on Cloud Run including download).
- **PV AG** (Proces-Verbal d'Assemblee Generale): Minutes from co-ownership meetings -- analyzed for risk flags, pending works, copropriete health.
- **Diagnostics**: Building diagnostics (amiante, plomb, DPE/GES energy ratings).
- **Redesign Studio**: AI-powered apartment photo transformation using Gemini image generation with style presets (modern_norwegian, minimalist_scandinavian, cozy_hygge).
- **Synthesis**: Cross-document aggregated analysis per property with cost breakdowns and risk assessments.
