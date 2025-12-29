# LangGraph Bulk Document Processing Implementation

## Overview

This document describes the implementation of the **LangGraph AI Agent** for intelligent bulk document processing. The agent automatically classifies, routes, processes, and synthesizes multiple documents in a single upload operation.

## Features

### 🤖 Intelligent Document Classification
- Automatically identifies document types (PV AG, diagnostics, taxes, charges)
- Routes each document to specialized processing agents
- No manual categorization required

### ⚡ Parallel Processing
- Processes multiple documents concurrently
- Distributed workflow orchestration via Temporal
- Efficient resource utilization

### 🧠 Cross-Document Synthesis
- Aggregates insights across all documents
- Generates comprehensive property summary
- Identifies risks, costs, and recommendations

### 📊 Progress Tracking
- Real-time workflow status
- Per-document processing state
- Overall completion percentage

## API Endpoints

### 1. Bulk Upload
```http
POST /api/v1/documents/bulk-upload
Content-Type: multipart/form-data

Form Fields:
- files: list[File] (max 50 files)
- property_id: int

Response (202 Accepted):
{
  "status": "processing",
  "workflow_id": "bulk-processing-123-1234567890",
  "workflow_run_id": "abc-def-ghi",
  "document_ids": [1, 2, 3, 4, 5],
  "total_files": 5,
  "message": "Successfully uploaded 5 documents..."
}
```

### 2. Bulk Status
```http
GET /api/v1/documents/bulk-status/{workflow_id}

Response (200 OK):
{
  "workflow_id": "bulk-processing-123-1234567890",
  "property_id": 123,
  "status": "running",
  "progress": {
    "total": 5,
    "completed": 3,
    "failed": 0,
    "processing": 2,
    "percentage": 60
  },
  "documents": [
    {
      "id": 1,
      "filename": "pv_ag_2024.pdf",
      "document_category": "pv_ag",
      "processing_status": "completed",
      "is_analyzed": true
    },
    ...
  ],
  "synthesis": {
    "summary": "Overall property analysis...",
    "total_annual_cost": 12500.0,
    "total_one_time_cost": 3500.0,
    "risk_level": "medium",
    "key_findings": [
      "Major roof renovation scheduled for 2025",
      "Asbestos detected in basement"
    ],
    "recommendations": [
      "Budget for €15,000 special assessment",
      "Request asbestos removal timeline"
    ]
  }
}
```

## Architecture

### Workflow Orchestration

```
User Upload (5 files)
        ↓
┌───────────────────────────────────┐
│  BulkDocumentProcessingWorkflow   │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│  1. Download from MinIO (parallel)│
│  2. Convert PDFs to images        │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│  3. LangGraph Agent               │
│     - Classification              │
│     - Routing                     │
│     - Processing (parallel)       │
│     - Synthesis                   │
└───────────────────────────────────┘
        ↓
┌───────────────────────────────────┐
│  4. Save results (parallel)       │
│     - Document analysis           │
│     - Document status             │
│     - Synthesis summary           │
└───────────────────────────────────┘
```

### LangGraph Agent Flow

```
documents[]
    ↓
┌────────────────┐
│  Classifier    │  ← Claude Sonnet 4.5
│  Agent         │     Identifies doc types
└────────────────┘
    ↓
┌────────────────┐
│  Router        │  ← Routes to specialists
└────────────────┘
    ↓  ↓  ↓  ↓
┌────┐┌────┐┌────┐┌────┐
│PV  ││Diag││Tax ││Chrg│ ← Specialized agents
│AG  ││    ││    ││    │   (parallel processing)
└────┘└────┘└────┘└────┘
    ↓  ↓  ↓  ↓
┌────────────────┐
│  Synthesis     │  ← Aggregates results
│  Agent         │     Generates insights
└────────────────┘
    ↓
Final Summary
```

## Database Schema Updates

### DocumentSummary Table Extensions

```sql
-- New fields for overall synthesis
overall_summary TEXT,              -- Cross-document summary
recommendations JSON,              -- Action items
risk_level VARCHAR,                -- low/medium/high
total_annual_cost FLOAT,          -- Alias for consistency
total_one_time_cost FLOAT,        -- Alias for consistency
synthesis_data JSON,               -- Full agent output
last_updated TIMESTAMP             -- Synthesis timestamp

-- Made nullable for flexibility
category VARCHAR NULL              -- Can be category-specific or overall
```

## Implementation Files

### New Files
1. **[backend/app/services/langgraph_agent_service.py](backend/app/services/langgraph_agent_service.py)**
   - LangGraph agent implementation
   - Document classification logic
   - Specialized processing agents
   - Synthesis generation

2. **[backend/scripts/generate_workflow_graph.py](backend/scripts/generate_workflow_graph.py)**
   - Visualize LangGraph workflow
   - Generate PNG/Mermaid diagrams

3. **[backend/alembic/versions/b2c3d4e5f6g7_add_langgraph_fields.py](backend/alembic/versions/b2c3d4e5f6g7_add_langgraph_fields.py)**
   - Database migration for new fields

### Modified Files
1. **[backend/app/api/documents.py](backend/app/api/documents.py:696-969)**
   - Added `/bulk-upload` endpoint
   - Added `/bulk-status/{workflow_id}` endpoint

2. **[backend/app/models/document.py](backend/app/models/document.py:75-106)**
   - Extended `DocumentSummary` model
   - Added synthesis fields

3. **[backend/app/workflows/activities.py](backend/app/workflows/activities.py:259-346)**
   - Added `run_langgraph_agent` activity
   - Added `save_document_synthesis` activity

4. **[backend/app/workflows/client.py](backend/app/workflows/client.py:108-145)**
   - Added `start_bulk_document_processing` method

5. **[backend/app/workflows/document_workflows.py](backend/app/workflows/document_workflows.py:193-349)**
   - Added `BulkDocumentProcessingWorkflow` class

6. **[backend/requirements.txt](backend/requirements.txt:25-34)**
   - Added `langgraph>=0.2.0`
   - Added `langchain-core>=0.1.0`
   - Added `pygraphviz>=1.11`
   - Added `graphviz>=0.20.1`

## Configuration

### Environment Variables

```bash
# Enable Temporal workflows (required for bulk processing)
ENABLE_TEMPORAL_WORKFLOWS=true

# Anthropic API key (for LangGraph agent)
ANTHROPIC_API_KEY=sk-ant-...

# MinIO configuration
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=appartment-docs

# Temporal configuration
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=appartment-agent
```

### VS Code MCP Server

Added LangChain documentation MCP server to [.vscode/settings.json](.vscode/settings.json:54-63):

```json
"mcp.servers": {
  "langchain-docs": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-langchain-docs"]
  }
}
```

## Usage Example

### Frontend Integration

```typescript
// Upload multiple documents at once
const formData = new FormData();
files.forEach(file => formData.append('files', file));
formData.append('property_id', propertyId.toString());

const response = await fetch('/api/v1/documents/bulk-upload', {
  method: 'POST',
  body: formData,
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const { workflow_id } = await response.json();

// Poll for status
const statusInterval = setInterval(async () => {
  const status = await fetch(`/api/v1/documents/bulk-status/${workflow_id}`);
  const data = await status.json();

  console.log(`Progress: ${data.progress.percentage}%`);

  if (data.status === 'completed') {
    clearInterval(statusInterval);
    console.log('Synthesis:', data.synthesis);
  }
}, 2000);
```

## Benefits

### For Users
- **Time Savings**: Upload all documents at once instead of one-by-one
- **No Manual Classification**: AI automatically identifies document types
- **Comprehensive Insights**: Get a holistic view across all documents
- **Risk Assessment**: Automatic identification of issues and costs

### For Developers
- **Scalable Architecture**: Temporal handles workflow orchestration
- **Parallel Processing**: Maximum efficiency with concurrent document processing
- **Extensible**: Easy to add new document types and specialized agents
- **Observable**: Full workflow tracking and debugging capabilities

## Testing

### Manual Testing
```bash
# 1. Start services
docker-compose up -d

# 2. Upload test documents
curl -X POST http://localhost:8000/api/v1/documents/bulk-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "property_id=123" \
  -F "files=@pv_ag.pdf" \
  -F "files=@diagnostic_amiante.pdf" \
  -F "files=@taxe_fonciere.pdf"

# 3. Check status
curl http://localhost:8000/api/v1/documents/bulk-status/{workflow_id} \
  -H "Authorization: Bearer $TOKEN"
```

### Visualize Workflow Graph
```bash
cd backend
python scripts/generate_workflow_graph.py
```

This generates a visual representation of the LangGraph agent workflow.

## Performance

### Processing Speed
- **Classification**: ~2-3 seconds per document
- **Analysis**: ~5-10 seconds per document (parallel)
- **Synthesis**: ~5-10 seconds total
- **Total**: ~15-25 seconds for 5 documents

### Cost Estimation (Claude API)
- **Classification**: ~500 tokens/document
- **Analysis**: ~2000 tokens/document
- **Synthesis**: ~1500 tokens
- **Total**: ~14,000 tokens for 5 documents ≈ $0.10

## Future Enhancements

1. **Smart Caching**: Reuse classification results for similar filenames
2. **Incremental Updates**: Only reprocess changed documents
3. **Custom Agents**: User-configurable processing rules
4. **Multi-Property Analysis**: Compare across multiple properties
5. **Export Reports**: Generate PDF/Excel summaries

## Related Documentation

- [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Overall implementation status
- [COMPLETE_STACK_MIGRATION.md](COMPLETE_STACK_MIGRATION.md) - Full stack migration guide
- [UV_MIGRATION_COMPLETE.md](UV_MIGRATION_COMPLETE.md) - UV dependency management
- [QUICK_START.md](QUICK_START.md) - Getting started guide

## Support

For issues or questions:
1. Check Temporal UI: http://localhost:8080
2. Check application logs: `docker-compose logs -f backend`
3. Review workflow execution in Temporal UI
4. Inspect LangGraph state in database `synthesis_data` field
