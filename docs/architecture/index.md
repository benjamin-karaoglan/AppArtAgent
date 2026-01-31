# Architecture

This section covers the system design and architecture of Appart Agent.

## Overview

Appart Agent follows a modern microservices architecture with clear separation of concerns:

- **Frontend**: Next.js 14 with App Router
- **Backend**: FastAPI with async processing
- **Storage**: Multi-backend support (MinIO/GCS)
- **AI Services**: Google Gemini for document analysis and image generation

## Sections

| Guide | Description |
|-------|-------------|
| [System Overview](overview.md) | High-level architecture and component interactions |
| [Data Flow](data-flow.md) | How data moves through the system |

## Design Principles

### 1. Separation of Concerns

Each layer has a specific responsibility:

- **API Layer**: Request handling, validation, routing
- **Service Layer**: Business logic, AI orchestration
- **Data Layer**: Database models, storage operations

### 2. Async-First

Background processing for:

- Document analysis
- Bulk uploads
- Image generation

### 3. Multi-Backend Storage

Abstracted storage interface supporting:

- MinIO for local development
- Google Cloud Storage for production

### 4. AI Provider Abstraction

Configurable AI backend:

- Google Gemini (default)
- Anthropic Claude (legacy support)
