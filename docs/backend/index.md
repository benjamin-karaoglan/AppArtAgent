# Backend

The AppArt Agent backend is a FastAPI application providing REST APIs for property analysis, document processing, and AI services.

## Overview

| Technology | Purpose |
|------------|---------|
| FastAPI | Async web framework |
| SQLAlchemy | ORM for PostgreSQL |
| Pydantic | Request/response validation |
| Google Generative AI | LLM integration |
| UV | Package management |

## Project Structure

```text
backend/
├── app/
│   ├── api/                 # REST API endpoints
│   │   ├── analysis.py      # Price analysis endpoints
│   │   ├── documents.py     # Document management (bulk delete, rename, synthesis)
│   │   ├── photos.py        # Photo upload, redesign, and promote/demote
│   │   ├── properties.py    # Property CRUD + with-synthesis endpoint
│   │   ├── users.py         # Authentication
│   │   └── webhooks.py      # Storage webhooks
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management (+ GCS_SIGNING_SERVICE_ACCOUNT)
│   │   ├── database.py      # Database connection
│   │   ├── better_auth_security.py  # Better Auth session validation
│   │   ├── i18n.py          # Internationalization (FR/EN)
│   │   ├── logging.py       # Logging setup
│   │   └── security.py      # Legacy JWT auth
│   ├── models/              # SQLAlchemy models
│   │   ├── analysis.py      # Analysis results (DocumentSummary)
│   │   ├── document.py      # Documents (storage_key/storage_bucket)
│   │   ├── photo.py         # Photos (promoted_redesign_id) and redesigns
│   │   ├── price_analysis.py  # Cached price analysis results
│   │   ├── property.py      # Properties and DVF (DVFSale, DVFSaleLot)
│   │   └── user.py          # Users
│   ├── schemas/             # Pydantic schemas
│   │   ├── document.py      # Document schemas (BulkDeleteRequest, RenameRequest)
│   │   ├── photo.py         # Photo schemas (PromotedRedesignResponse)
│   │   └── property.py      # Property schemas (PropertyUpdate, PropertyWithSynthesis)
│   ├── services/            # Business logic
│   │   ├── ai/              # AI services
│   │   │   ├── document_analyzer.py
│   │   │   ├── document_processor.py  # Native PDF + thinking
│   │   │   └── image_generator.py
│   │   ├── documents/       # Document processing
│   │   │   ├── bulk_processor.py      # Async parallel processing
│   │   │   └── parser.py
│   │   ├── dvf_service.py   # DVF price analysis and address matching
│   │   ├── price_analysis.py  # Price analysis caching service
│   │   └── storage.py       # Storage abstraction (MinIO/GCS)
│   ├── prompts/             # AI prompt templates
│   │   └── v1/              # Versioned prompts (incl. dp_process_other.md)
│   └── main.py              # Application entry
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
└── tests/                   # Test suite
```

## Sections

| Guide | Description |
|-------|-------------|
| [API Reference](api-reference.md) | All REST endpoints and schemas |
| [AI Services](ai-services.md) | Gemini integration and document analysis |
| [Prompt Templates](prompt-templates.md) | Versioned AI prompt management |
| [Database & Models](database.md) | Data models and migrations |
| [DVF Data](dvf-data.md) | French property data import and queries |

## Performance

- **Redis caching**: Expensive endpoints (`/dvf-stats`, `/price-analysis`, `/price-analysis/full`) are cached via the fault-tolerant `app/core/cache.py` module. Redis down = cache miss, never an error.
- **N+1 query fix**: `/api/properties/with-synthesis` uses batch fetches (4 queries total instead of 3N+1).
- **Load testing**: Locust-based load tests in `loadtest/locustfile.py` with `AppArtUser` and `FrontendUser` classes.

## Quick Commands

```bash
# Start backend (Docker)
docker-compose up backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# View logs
docker-compose logs -f backend

# Run tests
docker-compose exec backend pytest
```

## API Documentation

When running, API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
