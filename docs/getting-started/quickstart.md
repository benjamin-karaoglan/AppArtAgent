# Quick Start

Get AppArt Agent running in 5 minutes using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Google Cloud project with Vertex AI enabled, **or** a [Gemini API key](https://aistudio.google.com/) for quick start

!!! tip "AI Provider Options"
    - **Vertex AI (recommended)**: Set `GEMINI_USE_VERTEXAI=true` with a GCP project
    - **REST API key (quick start)**: Get a key from [Google AI Studio](https://aistudio.google.com/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/benjamin-karaoglan/appart-agent.git
cd appart-agent
```

### 2. Configure Environment

```bash
# Copy example environment files
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

Edit `.env` and configure AI + security:

```bash
SECRET_KEY=your-secret-key-at-least-32-characters-long

# Option A: Vertex AI (production)
GEMINI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=your-project-id

# Option B: REST API key (quick start)
GEMINI_USE_VERTEXAI=false
GOOGLE_CLOUD_API_KEY=your_api_key_here
```

Edit `frontend/.env.local` and set the Better Auth secret:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
DATABASE_URL=postgresql://appart:appart@db:5432/appart_agent
BETTER_AUTH_SECRET=$(openssl rand -hex 32)  # Generate a random secret
```

!!! tip "Google OAuth (optional)"
    To enable "Sign in with Google", add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
    to `frontend/.env.local`. See [Configuration](configuration.md#better-auth-setup) for setup steps.

### 3. Start Services

```bash
docker-compose up -d
```

This starts all services:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8000 | FastAPI application |
| API Docs | http://localhost:8000/docs | Swagger UI |
| MinIO Console | http://localhost:9001 | Storage management |

### 4. Verify Installation

Database migrations run automatically via the `db-migrate` service.

1. Open http://localhost:3000 in your browser
2. Register a new account
3. Create a property
4. Upload a test document

!!! success "You're ready!"
    The application is now running. Continue to explore features or set up development environment.

## Alternative: Use Google Cloud Storage

For local development with real GCS buckets (recommended for testing production parity):

```bash
# 1. Setup service account impersonation (one-time)
gcloud iam service-accounts add-iam-policy-binding \
  appart-backend@YOUR_PROJECT.iam.gserviceaccount.com \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=YOUR_PROJECT

# 2. Login with impersonation
gcloud auth application-default login \
  --impersonate-service-account=appart-backend@YOUR_PROJECT.iam.gserviceaccount.com

# 3. Configure .env
STORAGE_BACKEND=gcs
GCS_DOCUMENTS_BUCKET=your-documents-bucket
GCS_PHOTOS_BUCKET=your-photos-bucket
GOOGLE_CLOUD_PROJECT=your-project-id
GEMINI_USE_VERTEXAI=true

# 4. Start with GCS
./dev.sh start-gcs
```

See [Local Setup - GCS with Impersonation](../development/local-setup.md#google-cloud-storage-with-service-account-impersonation-recommended) for detailed instructions.

## Next Steps

- [Import DVF Data](../backend/dvf-data.md) for price analysis features
- [Configure AI Services](../backend/ai-services.md) for document analysis
- [Set up Hot Reload](../development/hot-reload.md) for development

## Troubleshooting

### Docker containers won't start

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker-compose logs db

# Restart database
docker-compose restart db
```

### AI/Gemini errors

1. If using API key: verify `GOOGLE_CLOUD_API_KEY` is set in `.env`
2. If using Vertex AI: verify `GEMINI_USE_VERTEXAI=true`, `GOOGLE_CLOUD_PROJECT` is set, and ADC is configured
3. Check API key or project has sufficient quota
4. Ensure billing is enabled on your Google Cloud project

### Port conflicts

If ports 3000, 8000, or 5432 are already in use:

```bash
# Find process using port
lsof -i :3000

# Or modify ports in docker-compose.yml
```

## Using the Dev Script

For convenience, use the included dev script:

```bash
# Start all services
./dev.sh start

# View logs
./dev.sh logs
./dev.sh logs backend  # Specific service

# Restart a service
./dev.sh restart backend

# Stop all services
./dev.sh stop

# View all commands
./dev.sh help
```
