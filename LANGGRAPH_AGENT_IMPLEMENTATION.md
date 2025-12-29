# LangGraph AI Agent for Document Management - Implementation Guide

## Overview

This document describes the implementation of an intelligent document processing system using **LangGraph**, which automatically classifies, routes, and processes multiple property documents in parallel.

## Key Features

### 1. **Intelligent Document Classification**
- Automatically identifies document types (PV AG, diagnostics, taxe foncière, charges)
- Uses Claude Vision API to analyze the first page
- Returns confidence scores and reasoning

### 2. **Smart Routing**
- Routes documents to specialized processing agents based on type
- Each document type has optimized prompts and extraction logic
- Handles subtypes (e.g., DPE, amiante, plomb for diagnostics)

### 3. **Parallel Processing**
- Processes multiple documents simultaneously using Temporal workflows
- Downloads from MinIO in parallel
- Converts PDFs to images in parallel
- Runs LangGraph agent for intelligent orchestration

### 4. **Comprehensive Synthesis**
- Aggregates results across all documents
- Calculates total costs (annual + one-time)
- Identifies key risks and concerns
- Provides actionable recommendations
- Organizes findings by category

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Bulk Upload Component                                 │  │
│  │  - Multi-file drag & drop                             │  │
│  │  - Progress tracking                                   │  │
│  │  - Real-time status updates                           │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│                                                               │
│  POST /api/documents/bulk-upload                            │
│  - Validates files                                           │
│  - Uploads to MinIO                                          │
│  - Creates document records                                  │
│  - Starts Temporal workflow                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Temporal Workflow (BulkDocumentProcessing)         │
│                                                               │
│  1. Download all files from MinIO (parallel)                 │
│  2. Convert PDFs to images (parallel)                        │
│  3. Run LangGraph Agent                                      │
│  4. Save results (parallel)                                  │
│  5. Save synthesis to DocumentSummary                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Agent Workflow                        │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Classify Documents                                 │  │
│  │     - Analyze first page with Claude                   │  │
│  │     - Determine type & confidence                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                      │                                        │
│                      ▼                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  2. Route to Specialized Processors                    │  │
│  │     - PV AG processor                                  │  │
│  │     - Diagnostic processor                             │  │
│  │     - Tax processor                                    │  │
│  │     - Charges processor                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                      │                                        │
│                      ▼                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  3. Process Documents (Parallel)                       │  │
│  │     - Extract structured data                          │  │
│  │     - Calculate costs                                  │  │
│  │     - Identify risks                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                      │                                        │
│                      ▼                                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  4. Synthesize Results                                 │  │
│  │     - Aggregate costs                                  │  │
│  │     - Identify patterns                                │  │
│  │     - Generate recommendations                         │  │
│  │     - Create comprehensive summary                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Files

### Backend

1. **`backend/app/services/langgraph_agent_service.py`** (NEW)
   - LangGraph workflow definition
   - Document classification logic
   - Specialized processors for each document type
   - Synthesis engine

2. **`backend/app/workflows/document_workflows.py`** (UPDATED)
   - Added `BulkDocumentProcessingWorkflow`
   - Parallel file downloads and conversions
   - Integration with LangGraph agent

3. **`backend/app/workflows/activities.py`** (UPDATED)
   - Added `run_langgraph_agent` activity
   - Added `save_document_synthesis` activity

4. **`backend/app/workflows/client.py`** (UPDATED)
   - Added `start_bulk_document_processing` method

5. **`backend/app/api/documents.py`** (UPDATED)
   - Added `/bulk-upload` endpoint
   - Added `/bulk-status/{workflow_id}` endpoint

6. **`backend/app/models/document.py`** (UPDATED)
   - Extended `DocumentSummary` model with new fields:
     - `overall_summary`
     - `risk_level`
     - `recommendations`
     - `synthesis_data`

7. **`backend/requirements.txt`** (UPDATED)
   - Added `langgraph>=0.2.0`
   - Added `langchain-core>=0.1.0`

### Configuration

8. **`.vscode/settings.json`** (UPDATED)
   - Added MCP server configuration for LangChain docs

9. **`.vscode/mcp.json`** (NEW)
   - MCP server configuration

## API Endpoints

### 1. Bulk Upload
```http
POST /api/documents/bulk-upload
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf, ...]
property_id: 123
```

**Response:**
```json
{
  "status": "processing",
  "workflow_id": "bulk-processing-123-1234567890",
  "workflow_run_id": "abc123...",
  "document_ids": [101, 102, 103],
  "total_files": 3,
  "message": "Successfully uploaded 3 documents..."
}
```

### 2. Check Bulk Status
```http
GET /api/documents/bulk-status/{workflow_id}
```

**Response:**
```json
{
  "workflow_id": "bulk-processing-123-1234567890",
  "property_id": 123,
  "status": "completed",
  "progress": {
    "total": 5,
    "completed": 5,
    "failed": 0,
    "processing": 0,
    "percentage": 100
  },
  "documents": [
    {
      "id": 101,
      "filename": "pv_ag_2024.pdf",
      "document_category": "pv_ag",
      "processing_status": "completed",
      "is_analyzed": true
    }
  ],
  "synthesis": {
    "summary": "Overall assessment...",
    "total_annual_cost": 3500.0,
    "total_one_time_cost": 15000.0,
    "risk_level": "medium",
    "key_findings": ["Finding 1", "Finding 2"],
    "recommendations": ["Rec 1", "Rec 2"]
  }
}
```

## LangGraph Workflow States

### Document Processing State
```python
class DocumentProcessingState(TypedDict):
    # Input
    documents: List[Dict[str, Any]]
    property_id: int

    # Classification
    classified_documents: List[Dict[str, Any]]

    # Processing
    processing_results: List[Dict[str, Any]]

    # Synthesis
    synthesis: Dict[str, Any]

    # Metadata
    errors: List[str]
    total_tokens: int
    total_cost: float
```

## Workflow Nodes

1. **classify_documents**
   - Analyzes first page of each document
   - Returns document type, confidence, reasoning

2. **process_pv_ag**
   - Extracts meeting minutes data
   - Identifies upcoming works and costs

3. **process_diagnostic**
   - Analyzes diagnostic reports
   - Extracts ratings, issues, remediation costs

4. **process_tax**
   - Extracts tax amounts and property values

5. **process_charges**
   - Extracts charges and breakdowns

6. **synthesize_results**
   - Aggregates all results
   - Calculates totals
   - Generates recommendations

## Database Schema Updates

### DocumentSummary Table (New Fields)
```sql
ALTER TABLE document_summaries
ADD COLUMN overall_summary TEXT,
ADD COLUMN risk_level VARCHAR(50),
ADD COLUMN recommendations JSON,
ADD COLUMN total_annual_cost FLOAT,
ADD COLUMN total_one_time_cost FLOAT,
ADD COLUMN synthesis_data JSON,
ADD COLUMN last_updated TIMESTAMP;
```

## Frontend Implementation

### Bulk Upload Component Features

1. **Drag & Drop Interface**
   - Multi-file selection
   - Visual file previews
   - File size validation

2. **Upload Progress**
   - Individual file progress
   - Overall progress percentage
   - Estimated time remaining

3. **Real-time Status**
   - WebSocket or polling for status updates
   - Live classification results
   - Processing progress per document

4. **Results Display**
   - Organized by document category
   - Summary cards with key metrics
   - Download processed documents
   - View synthesis report

### Example Usage Flow

1. User selects property
2. Drags and drops 10 PDF files
3. System uploads to MinIO instantly
4. LangGraph agent classifies:
   - 3x PV d'AG
   - 4x Diagnostics (2 DPE, 1 amiante, 1 plomb)
   - 1x Taxe foncière
   - 2x Charges
5. All documents processed in parallel
6. Synthesis generated:
   - Total annual costs: €3,500
   - One-time costs: €15,000
   - Risk level: Medium
   - Key findings: 5 items
   - Recommendations: 3 actions

## Benefits

### For Users
- **Zero Configuration**: Just upload files, agent handles the rest
- **Time Savings**: Process 10+ documents in minutes vs. hours
- **Comprehensive Analysis**: Synthesis across all documents
- **Better Insights**: AI identifies patterns and risks

### For Developers
- **Scalable**: Parallel processing with Temporal
- **Maintainable**: Clear separation of concerns
- **Extensible**: Easy to add new document types
- **Observable**: Full workflow tracking and logging

## Configuration

### Environment Variables
```bash
# LangChain/LangGraph
ANTHROPIC_API_KEY=sk-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Temporal
ENABLE_TEMPORAL_WORKFLOWS=true
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=document-processing

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=documents
```

## Testing

### 1. Test Bulk Upload
```bash
curl -X POST http://localhost:8000/api/documents/bulk-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "property_id=1" \
  -F "files=@pv_ag.pdf" \
  -F "files=@dpe.pdf" \
  -F "files=@taxe.pdf"
```

### 2. Monitor Status
```bash
curl http://localhost:8000/api/documents/bulk-status/bulk-processing-1-1234567890 \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

1. **Database Migration**: Create Alembic migration for DocumentSummary updates
2. **Frontend Component**: Build React component for bulk upload UI
3. **WebSocket Support**: Add real-time progress updates
4. **Error Handling**: Enhance retry logic and error recovery
5. **Testing**: Add unit and integration tests
6. **Documentation**: Add API documentation with examples

## Performance Considerations

- **Parallel Processing**: All documents processed simultaneously
- **Chunking**: Large batches split into manageable chunks
- **Caching**: LangGraph state checkpointing for resumability
- **Resource Limits**: Max 50 files per bulk upload
- **Token Optimization**: Single-page classification vs. full document parsing

## Cost Estimation

### Per Document (Average)
- Classification: ~500 tokens (~$0.002)
- Processing: 2,000-5,000 tokens (~$0.01-$0.03)
- Synthesis (per batch): ~1,000 tokens (~$0.005)

### Bulk Upload (10 Documents)
- Total tokens: ~30,000-50,000
- Total cost: ~$0.15-$0.30

## Monitoring & Logging

All components include comprehensive logging:
- Request/response logging
- Workflow state transitions
- Agent decision reasoning
- Error tracking with stack traces
- Performance metrics (tokens, cost, duration)

---

**Status**: ✅ Backend implemented, ready for frontend integration
**Next**: Frontend bulk upload UI + database migration
