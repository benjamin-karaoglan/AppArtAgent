# Data Flow

This document describes how data flows through the AppArt Agent system for key operations.

## Document Upload and Analysis

The bulk document upload flow demonstrates the async processing architecture:

```mermaid
sequenceDiagram
    participant User as User Browser
    participant FE as Frontend (Next.js)
    participant BE as Backend (FastAPI)
    participant Store as Storage (MinIO)
    participant AI as AI (Gemini)

    User->>FE: 1. Select files
    FE->>BE: 2. POST /bulk-upload
    BE->>Store: 3. Store files
    BE->>BE: 4. Create DB records
    BE-->>FE: 5. Return workflow_id
    FE-->>User: 6. Show progress

    Note over BE,AI: Background Processing
    BE->>AI: 7. Classify documents
    AI-->>BE: 8. Classification results
    BE->>AI: 9. Parallel: Analyze each
    AI-->>BE: 10. Analysis results
    BE->>AI: 11. Synthesize all documents
    AI-->>BE: 12. Final synthesis

    FE->>BE: 13. Poll status
    BE-->>FE: 14. Complete
    FE-->>User: Display results
```

### Processing Stages

1. **Upload**: Files sent via multipart form data
2. **Storage**: Files stored in MinIO with SHA-256 hash for deduplication
3. **Classification**: AI identifies document types (PV AG, diagnostic, tax, charges)
4. **Analysis**: Parallel processing with type-specific prompts
5. **Synthesis**: Cross-document analysis aggregating costs and risks

## Price Analysis Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant FE as Frontend (Next.js)
    participant BE as Backend (FastAPI)
    participant DB as PostgreSQL (DVF)

    User->>FE: 1. Enter address
    FE->>BE: 2. GET /analysis
    BE->>DB: 3. Query DVF records
    DB-->>BE: 4. Raw results
    BE->>BE: 5. Apply IQR filtering
    BE->>BE: 6. Calculate trends
    BE-->>FE: 7. Return analysis
    FE-->>User: 8. Display results
```

### Analysis Types

| Type | Data Source | Purpose |
|------|-------------|---------|
| Simple | Exact address matches | Historical sales at property |
| Trend | Neighboring properties | Price evolution and projections |
| Market | Area-wide data | Comparative market analysis |

## Photo Redesign Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant FE as Frontend (Next.js)
    participant BE as Backend (FastAPI)
    participant Store as Storage (MinIO)
    participant AI as AI (Gemini)

    User->>FE: 1. Upload photo
    FE->>BE: 2. POST /photos
    BE->>Store: 3. Store original
    BE-->>FE: 4. Return photo_id
    User->>FE: 5. Select style
    FE->>BE: 6. POST /redesign
    BE->>AI: 7. Generate image
    AI-->>BE: 8. Return redesign
    BE->>Store: 9. Store result
    BE-->>FE: 10. Return presigned URL
    FE-->>User: 11. Display redesign
```

## Authentication Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant FE as Frontend (Next.js)
    participant BE as Backend (FastAPI)
    participant DB as PostgreSQL (Users)

    User->>FE: 1. Submit login
    FE->>BE: 2. POST /auth/login
    BE->>DB: 3. Verify password
    DB-->>BE: 4. User record
    BE->>BE: 5. Generate JWT
    BE-->>FE: 6. Return token
    FE->>FE: 7. Store token
    FE-->>User: 8. Redirect dashboard
```

## Data Processing Pipeline

```mermaid
flowchart LR
    subgraph Upload["1. Upload"]
        A[Files] --> B[Multipart Form]
    end

    subgraph Storage["2. Storage"]
        B --> C[SHA-256 Hash]
        C --> D[MinIO]
    end

    subgraph Classification["3. Classification"]
        D --> E[First Page Image]
        E --> F[Gemini Vision]
        F --> G[Document Type]
    end

    subgraph Analysis["4. Analysis"]
        G --> H[Type-specific Prompts]
        H --> I[Parallel Processing]
        I --> J[Structured Results]
    end

    subgraph Synthesis["5. Synthesis"]
        J --> K[Aggregate Costs]
        K --> L[Risk Assessment]
        L --> M[Recommendations]
    end
```

## Data Consistency

### Transaction Boundaries

- Document uploads: Single transaction for record creation
- Bulk processing: Per-document transactions with rollback capability
- DVF imports: Chunked transactions (30k records per batch)

### Caching Strategy

| Data | Cache | TTL | Invalidation |
|------|-------|-----|--------------|
| User sessions | Redis | 7 days | On logout |
| DVF queries | Redis | 1 hour | Time-based |
| Document metadata | PostgreSQL | N/A | On update |
| File content | MinIO/GCS | N/A | Manual delete |
