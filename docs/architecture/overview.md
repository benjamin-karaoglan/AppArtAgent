# System Overview

## High-Level Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["Client Layer"]
        Browser["Web Browser<br/>• Dashboard views<br/>• Document uploads<br/>• Photo redesign"]
    end

    subgraph FrontendLayer["Frontend Layer - Next.js 14"]
        subgraph Pages["Pages"]
            P1[Dashboard]
            P2[Properties]
            P3[Documents]
            P4[Photos]
        end
        subgraph Components["Components"]
            C1[Header]
            C2[Charts]
            C3[Tooltips]
            C4[Forms]
        end
        subgraph APIClient["API Client"]
            AC1[React Query]
            AC2[Type-safe fetching]
        end
    end

    subgraph BackendLayer["Backend Layer - FastAPI"]
        subgraph Endpoints["API Endpoints"]
            E1["/api/users"]
            E2["/api/properties"]
            E3["/api/documents"]
            E4["/api/analysis"]
            E5["/api/photos"]
        end
        subgraph Services["Service Layer"]
            S1["AI Services<br/>Analyzer, Processor, ImageGen"]
            S2["Storage<br/>MinIO, GCS"]
            S3["Document Processing<br/>Parser, Bulk Processor"]
            S4["DVF Service<br/>Import, Search"]
            S5["Price Analysis<br/>Trends"]
        end
    end

    subgraph DataLayer["Data Layer"]
        PostgreSQL[("PostgreSQL<br/>• Users<br/>• Properties<br/>• Documents<br/>• DVF Data (5.4M+)")]
        Redis[("Redis<br/>• Cache<br/>• Sessions")]
        Storage[("MinIO / GCS<br/>• Documents<br/>• Photos")]
    end

    Browser --> FrontendLayer
    FrontendLayer -->|"HTTP/REST"| BackendLayer
    Services --> PostgreSQL
    Services --> Redis
    Services --> Storage
```

## Component Details

### Frontend (Next.js 14)

| Directory | Purpose |
|-----------|---------|
| `src/app/` | App Router pages and layouts |
| `src/components/` | Reusable React components |
| `src/contexts/` | React context providers (Auth) |
| `src/lib/` | Utilities and API client |
| `src/types/` | TypeScript type definitions |

**Key Technologies**:

- React 18 with Server Components
- Tailwind CSS for styling
- React Query for data fetching
- TypeScript for type safety

### Backend (FastAPI)

| Directory | Purpose |
|-----------|---------|
| `app/api/` | REST API route handlers |
| `app/core/` | Configuration, database, security |
| `app/models/` | SQLAlchemy ORM models |
| `app/schemas/` | Pydantic request/response schemas |
| `app/services/` | Business logic and integrations |
| `app/prompts/` | AI prompt templates |

**Key Technologies**:

- FastAPI for async HTTP handling
- SQLAlchemy for ORM
- Pydantic for validation
- Google Generative AI SDK

### Data Layer

#### PostgreSQL

Stores structured data:

- User accounts and authentication
- Properties and their metadata
- Documents and analysis results
- DVF records (5.4M+ property transactions)

#### Redis

In-memory caching for:

- Session data
- Frequently accessed queries
- Rate limiting

#### MinIO / Google Cloud Storage

Object storage for:

- Uploaded documents (PDF, images)
- Generated images (photo redesigns)
- Presigned URLs for secure access

## Service Dependencies

```mermaid
graph TD
    Frontend[Frontend] --> Backend[Backend API]
    Backend --> PostgreSQL[(PostgreSQL)]
    Backend --> Redis[(Redis)]
    Backend --> Storage[(MinIO/GCS)]
    Backend --> Gemini[Gemini AI]
    
    subgraph External
        Gemini
    end
    
    subgraph Data
        PostgreSQL
        Redis
        Storage
    end
```

## Security Architecture

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant DB as PostgreSQL

    User->>Frontend: Submit credentials
    Frontend->>Backend: POST /auth/login
    Backend->>DB: Verify password
    DB-->>Backend: User record
    Backend->>Backend: Generate JWT
    Backend-->>Frontend: Return token
    Frontend->>Frontend: Store token
    Frontend-->>User: Redirect to dashboard
```

### API Security

- **CORS**: Restricted to allowed origins
- **Rate Limiting**: Redis-based request throttling
- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: SQLAlchemy parameterized queries

### Storage Security

- **MinIO**: Access keys for authentication
- **GCS**: Service account with IAM roles
- **Presigned URLs**: Time-limited access to files
