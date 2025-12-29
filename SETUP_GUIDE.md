# LangGraph AI Agent - Complete Setup Guide

This guide will walk you through installing dependencies, running migrations, and testing the new LangGraph-based bulk document processing system.

## Prerequisites

- Docker and Docker Compose (for services)
- Python 3.10+ (backend)
- Node.js 18+ (frontend)
- Graphviz system library (for graph visualization)

## Step 1: Install System Dependencies

### macOS
```bash
# Install Graphviz (required for graph visualization)
brew install graphviz

# Verify installation
dot -V  # Should show graphviz version
```

### Linux (Ubuntu/Debian)
```bash
# Install Graphviz
sudo apt-get update
sudo apt-get install -y graphviz graphviz-dev

# Verify installation
dot -V
```

### Windows
```powershell
# Install via Chocolatey
choco install graphviz

# Or download from: https://graphviz.org/download/
```

## Step 2: Install Python Dependencies

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows

# Install new dependencies
pip install langgraph>=0.2.0 langchain-core>=0.1.0

# Install graph visualization dependencies
pip install pygraphviz>=1.11 graphviz>=0.20.1

# Or install all at once
pip install -r requirements.txt
```

### Troubleshooting pygraphviz Installation

If you encounter errors installing pygraphviz:

**macOS:**
```bash
# Set compiler flags
export CFLAGS="-I$(brew --prefix graphviz)/include"
export LDFLAGS="-L$(brew --prefix graphviz)/lib"
pip install pygraphviz
```

**Linux:**
```bash
# Install dev packages
sudo apt-get install -y python3-dev pkg-config
pip install pygraphviz
```

**If still failing:** pygraphviz is optional for PNG export. The system will fall back to ASCII text graphs.

## Step 3: Start Required Services

```bash
# Start all services (PostgreSQL, MinIO, Temporal)
docker-compose up -d

# Wait for services to be ready (~10 seconds)
sleep 10

# Verify services are running
docker-compose ps

# Expected output:
# - db (PostgreSQL): Up
# - minio: Up
# - temporal: Up
```

## Step 4: Run Database Migration

```bash
cd backend
source venv/bin/activate

# Run the migration
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade a1b2c3d4e5f6 -> b2c3d4e5f6g7, Add LangGraph agent fields to DocumentSummary
```

### Verify Migration
```bash
# Connect to database
docker-compose exec db psql -U postgres -d appartment_agent

# Check new columns
\d document_summaries

# You should see:
# - overall_summary (text)
# - recommendations (json)
# - total_annual_cost (double precision)
# - total_one_time_cost (double precision)
# - risk_level (varchar)
# - synthesis_data (json)
# - last_updated (timestamp)
```

## Step 5: Generate Workflow Graph

```bash
cd backend
source venv/bin/activate

# Run the graph generation script
python scripts/generate_workflow_graph.py

# This will create:
# - docs/langgraph_workflow.png (visual diagram)
# - docs/langgraph_workflow_ascii.txt (text version)
```

Expected ASCII output:
```
            +-----------+
            | __start__ |
            +-----------+
                   *
                   *
                   *
        +----------------------+
        | classify_documents  |
        +----------------------+
          *       *      *      *
       ***       **     **      ****
      **        **     **          *
+--------+ +-------+ +-----+ +--------+
|pv_ag  | |diag   | |tax  | |charges |
+--------+ +-------+ +-----+ +--------+
      **         **    **         **
       **         **  **         **
         *         ****         *
         +--------------------+
         | synthesize_results |
         +--------------------+
                    *
                    *
                    *
             +---------+
             | __end__ |
             +---------+
```

## Step 6: Test the System

### Start Backend Services

```bash
# Terminal 1: Start Temporal worker
cd backend
source venv/bin/activate
export ENABLE_TEMPORAL_WORKFLOWS=true
python -m app.workflows.worker

# Terminal 2: Start FastAPI backend
cd backend
source venv/bin/activate
export ENABLE_TEMPORAL_WORKFLOWS=true
uvicorn app.main:app --reload --port 8000
```

### Test Bulk Upload API

```bash
# Create test files (in a new terminal)
cd /tmp
echo "PV d'AG test content" > pv_ag_test.pdf
echo "DPE test content" > dpe_test.pdf
echo "Taxe foncière test content" > taxe_test.pdf

# Get auth token (replace with your actual login)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  | jq -r '.access_token')

# Upload documents in bulk
curl -X POST http://localhost:8000/api/documents/bulk-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "property_id=1" \
  -F "files=@/tmp/pv_ag_test.pdf" \
  -F "files=@/tmp/dpe_test.pdf" \
  -F "files=@/tmp/taxe_test.pdf"

# Expected response:
{
  "status": "processing",
  "workflow_id": "bulk-processing-1-1234567890",
  "workflow_run_id": "abc123...",
  "document_ids": [101, 102, 103],
  "total_files": 3,
  "message": "Successfully uploaded 3 documents. The AI agent is now classifying and processing them..."
}
```

### Monitor Processing

```bash
# Save the workflow_id from previous response
WORKFLOW_ID="bulk-processing-1-1234567890"

# Check status
curl http://localhost:8000/api/documents/bulk-status/$WORKFLOW_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'

# Expected response:
{
  "workflow_id": "bulk-processing-1-1234567890",
  "property_id": 1,
  "status": "completed",
  "progress": {
    "total": 3,
    "completed": 3,
    "failed": 0,
    "processing": 0,
    "percentage": 100
  },
  "documents": [...],
  "synthesis": {
    "summary": "Comprehensive analysis...",
    "total_annual_cost": 3500.0,
    "total_one_time_cost": 15000.0,
    "risk_level": "medium",
    "key_findings": [...],
    "recommendations": [...]
  }
}
```

### Check Logs

```bash
# Backend logs
tail -f backend/logs/app.log

# Worker logs
tail -f backend/logs/worker.log

# Temporal logs
docker-compose logs -f temporal
```

## Step 7: Test Graph Visualization in Code

Create a test script:

```python
# test_graph.py
from app.services.langgraph_agent_service import get_langgraph_agent

# Initialize agent
agent = get_langgraph_agent()

# Export as PNG
png_path = agent.export_graph_as_png("test_workflow.png")
print(f"Graph saved to: {png_path}")

# Get ASCII representation
ascii_graph = agent.get_graph_ascii()
print(ascii_graph)
```

Run it:
```bash
cd backend
source venv/bin/activate
python test_graph.py
```

## Configuration

### Environment Variables

Create/update `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appartment_agent

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...
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
MINIO_SECURE=false

# Other
UPLOAD_DIR=/tmp/uploads
ALLOWED_EXTENSIONS=[".pdf", ".jpg", ".jpeg", ".png"]
```

## Verification Checklist

- [ ] Graphviz installed (`dot -V` works)
- [ ] Python dependencies installed (`pip list | grep langgraph`)
- [ ] Docker services running (`docker-compose ps`)
- [ ] Database migration applied (`alembic current`)
- [ ] Workflow graph generated successfully
- [ ] Backend starts without errors
- [ ] Temporal worker connects successfully
- [ ] Bulk upload API works
- [ ] Documents are classified correctly
- [ ] Synthesis is generated
- [ ] PNG graph can be exported (or ASCII fallback works)

## Troubleshooting

### Issue: "Module not found: langgraph"
**Solution**: Install dependencies
```bash
cd backend && source venv/bin/activate
pip install langgraph langchain-core
```

### Issue: "pygraphviz failed to build"
**Solution**: Either install graphviz system library, or accept ASCII-only fallback
```bash
# macOS
brew install graphviz
export CFLAGS="-I$(brew --prefix graphviz)/include"
export LDFLAGS="-L$(brew --prefix graphviz)/lib"
pip install pygraphviz

# Or skip it - ASCII graphs will work
```

### Issue: "could not translate host name 'db'"
**Solution**: Start Docker services
```bash
docker-compose up -d
```

### Issue: "Temporal worker not connecting"
**Solution**: Check Temporal service
```bash
docker-compose logs temporal
docker-compose restart temporal
```

### Issue: "Documents stuck in 'processing' status"
**Solution**: Check worker logs
```bash
# Worker must be running
python -m app.workflows.worker

# Check logs
tail -f backend/logs/app.log
```

### Issue: "LangGraph agent returning errors"
**Solution**: Check Anthropic API key
```bash
# Verify API key is set
echo $ANTHROPIC_API_KEY

# Test with curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-5-20250929",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Next Steps

1. **Frontend Integration**: Build the bulk upload UI component
2. **Monitoring**: Set up dashboard for workflow monitoring
3. **Testing**: Add unit and integration tests
4. **Deployment**: Deploy to production environment
5. **Optimization**: Tune agent prompts based on real documents

## Resources

- [LangGraph Documentation](https://docs.langchain.com/langgraph)
- [Temporal Documentation](https://docs.temporal.io/)
- [MinIO Documentation](https://min.io/docs/)
- [Project Implementation Guide](./LANGGRAPH_AGENT_IMPLEMENTATION.md)

## Support

If you encounter issues:
1. Check the logs (`backend/logs/`)
2. Review the troubleshooting section above
3. Check the [Implementation Guide](./LANGGRAPH_AGENT_IMPLEMENTATION.md)
4. Open an issue with logs and error messages
