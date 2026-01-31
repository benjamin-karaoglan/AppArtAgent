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

```
backend/
├── app/
│   ├── api/                 # REST API endpoints
│   │   ├── analysis.py      # Price analysis endpoints
│   │   ├── documents.py     # Document management
│   │   ├── photos.py        # Photo upload and redesign
│   │   ├── properties.py    # Property CRUD
│   │   ├── users.py         # Authentication
│   │   └── webhooks.py      # MinIO webhooks
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   ├── database.py      # Database connection
│   │   ├── logging.py       # Logging setup
│   │   └── security.py      # Auth utilities
│   ├── models/              # SQLAlchemy models
│   │   ├── analysis.py      # Analysis results
│   │   ├── document.py      # Documents
│   │   ├── photo.py         # Photos and redesigns
│   │   ├── property.py      # Properties and DVF
│   │   └── user.py          # Users
│   ├── schemas/             # Pydantic schemas
│   │   ├── document.py      # Document schemas
│   │   ├── photo.py         # Photo schemas
│   │   └── property.py      # Property schemas
│   ├── services/            # Business logic
│   │   ├── ai/              # AI services
│   │   │   ├── document_analyzer.py
│   │   │   ├── document_processor.py
│   │   │   └── image_generator.py
│   │   ├── documents/       # Document processing
│   │   │   ├── bulk_processor.py
│   │   │   └── parser.py
│   │   ├── dvf_service.py   # DVF data management
│   │   ├── price_analysis.py
│   │   └── storage.py       # MinIO/GCS abstraction
│   ├── prompts/             # AI prompt templates
│   │   └── v1/              # Versioned prompts
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
| [Database & Models](database.md) | Data models and migrations |
| [DVF Data](dvf-data.md) | French property data import and queries |

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
