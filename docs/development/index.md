# Development

This section covers local development setup, workflows, and contributing guidelines.

## Overview

| Guide | Description |
|-------|-------------|
| [Local Setup](local-setup.md) | Setting up development environment |
| [Hot Reload](hot-reload.md) | Development workflow with live reload |
| [Testing](testing.md) | Running and writing tests |
| [Contributing](contributing.md) | Guidelines for contributors |

## Quick Start

```bash
# Start development environment
./dev.sh start

# View logs
./dev.sh logs

# Stop services
./dev.sh stop
```

## Development Stack

### Backend

| Tool | Purpose |
|------|---------|
| UV | Python package management (75x faster) |
| FastAPI | Async web framework |
| Alembic | Database migrations |
| pytest | Testing framework |

### Frontend

| Tool | Purpose |
|------|---------|
| pnpm | JavaScript package management (5-10x faster) |
| Next.js 14 | React framework |
| TypeScript | Type safety |
| ESLint | Code linting |

## Development Philosophy

1. **Type Safety**: TypeScript (frontend) and Pydantic (backend)
2. **Code Quality**: Linting and formatting enforced
3. **Fast Feedback**: Hot reload for instant changes
4. **Test Coverage**: Unit and integration tests
