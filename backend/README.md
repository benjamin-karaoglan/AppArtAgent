# AppArt Agent Backend

AI-powered apartment purchasing decision platform for France - Backend API

## Features

- **Async Document Processing**: Upload documents for background processing with async processor
- **MinIO Object Storage**: S3-compatible object storage with file deduplication and presigned URLs
- **Gemini AI Integration**: Google Gemini for document analysis with multimodal vision support
- **Multimodal Document Parsing**: Uses Gemini's vision capabilities to parse PDF documents (diagnostics, PV d'AG, tax documents)
- **Photo Redesign Studio**: AI-powered apartment photo redesign using Gemini image generation
- **Comprehensive Logging**: Full logging support with file rotation and error tracking
- **Fast Dependency Management**: Uses `uv` for lightning-fast package installation
- **RESTful API**: FastAPI-based backend with automatic OpenAPI documentation

## Quick Start

### Using Docker (Recommended)

```bash
# From the root directory
docker-compose up
```

### Local Development with uv

1. Install uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies:

```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

3. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:

```bash
uvicorn app.main:app --reload
```

## Configuration

Key environment variables (set in `.env`):

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for legacy auth (32+ chars)
- `GEMINI_USE_VERTEXAI`: `true` for Vertex AI (production), `false` for REST API key (dev)
- `GOOGLE_CLOUD_API_KEY`: Gemini REST API key (only when `GEMINI_USE_VERTEXAI=false`)
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (required for Vertex AI)
- `GOOGLE_CLOUD_LOCATION`: GCP region (default: us-central1)
- `GEMINI_LLM_MODEL`: Text analysis model (default: gemini-2.5-flash)
- `GEMINI_IMAGE_MODEL`: Image generation model (default: gemini-2.5-flash-image)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `STORAGE_BACKEND`: `minio` (dev) or `gcs` (production)
- `MINIO_ENDPOINT`: MinIO server endpoint (default: minio:9000)
- `MINIO_ACCESS_KEY`: MinIO access key (default: minioadmin)
- `MINIO_SECRET_KEY`: MinIO secret key (default: minioadmin)

## Logging

Logs are stored in the `logs/` directory:

- `app.log`: All application logs with rotation (10MB max, 5 backups)
- `errors.log`: Error-level logs only

## Document Processing

### Single Document Upload

The endpoint for immediate processing:

1. **Upload**: Documents are uploaded via `/api/documents/upload`
2. **PDF to Images**: PDFs are converted to high-quality images
3. **Multimodal Analysis**: Images are sent to Gemini for analysis
4. **Structured Extraction**: Results are parsed and stored in the database

### Bulk Upload (Recommended)

For processing multiple documents with intelligent classification:

1. **Upload**: Multiple files uploaded via `/api/documents/bulk-upload`
2. **MinIO Storage**: Files are stored in MinIO object storage
3. **Auto-Classification**: Gemini automatically classifies document types
4. **Parallel Processing**: Documents processed concurrently
5. **Synthesis**: Results aggregated into comprehensive property summary
6. **Status Tracking**: Monitor progress via `/api/documents/bulk-status/{workflow_id}`

**Architecture Benefits**:

- **Auto-Classification**: AI automatically determines document types
- **Batch Processing**: Upload all property documents at once
- **Synthesis**: Get comprehensive property analysis from all documents
- **Deduplication**: SHA-256 file hashing prevents duplicate processing

Supported document types:

- **PV d'AG**: Assembly meeting minutes
- **Diagnostics**: DPE, amiante, plomb, termite, electric, gas
- **Tax documents**: Taxe foncière
- **Charges**: Condominium charges

## API Documentation

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## DVF Data Management

### Current Database

The database contains **5.4 million DVF property records** across 4 years (2022-2025 Q1-Q2).

### Importing DVF Data

```bash
# Import a specific year (using Docker)
docker-compose exec backend python scripts/import_dvf_chunked.py \
  data/dvf/ValeursFoncieres-2024.txt --year 2024

# Import with custom chunk size for memory-constrained environments
docker-compose exec backend python scripts/import_dvf_chunked.py \
  data/dvf/ValeursFoncieres-2023.txt --year 2023 --read-chunk-size 30000

# Force re-import (bypasses file hash check)
docker-compose exec backend python scripts/import_dvf_chunked.py \
  data/dvf/ValeursFoncieres-2024.txt --year 2024 --force
```

### Migration Management

Database migrations are managed with Alembic:

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Check current migration version
docker-compose exec backend alembic current

# Rollback one migration
docker-compose exec backend alembic downgrade -1
```

### Import Management

```bash
# View import history
docker-compose exec backend python scripts/rollback_dvf_import.py --list

# Rollback a specific import
docker-compose exec backend python scripts/rollback_dvf_import.py <batch_id>

# Check database status
docker-compose exec db psql -U appart -d appart_agent -c \
  "SELECT data_year, COUNT(*) as records FROM dvf_records GROUP BY data_year ORDER BY data_year;"
```

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov

# Run DVF service tests specifically
uv run pytest tests/test_dvf_service.py -v
```
