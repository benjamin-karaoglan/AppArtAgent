# 🚀 Quick Start - LangGraph AI Agent

Get up and running in 5 minutes!

## Prerequisites
- Docker running
- Python 3.10+ venv activated
- Anthropic API key

## Installation (2 minutes)

```bash
# 1. Install graphviz (for graph visualization)
brew install graphviz  # macOS
# sudo apt-get install graphviz  # Linux

# 2. Install Python dependencies
cd backend && source venv/bin/activate
pip install langgraph langchain-core langchain-anthropic

# Optional: for PNG graph export
pip install pygraphviz graphviz

# 3. Start services
docker-compose up -d

# 4. Run migration
alembic upgrade head
```

## Test It (3 minutes)

```bash
# 1. Generate workflow graph
python scripts/generate_workflow_graph.py

# 2. Start worker (Terminal 1)
export ENABLE_TEMPORAL_WORKFLOWS=true
python -m app.workflows.worker

# 3. Start API (Terminal 2)
export ENABLE_TEMPORAL_WORKFLOWS=true
uvicorn app.main:app --reload

# 4. Test bulk upload (Terminal 3)
curl -X POST http://localhost:8000/api/documents/bulk-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "property_id=1" \
  -F "files=@test1.pdf" \
  -F "files=@test2.pdf" \
  -F "files=@test3.pdf"

# 5. Check status
curl http://localhost:8000/api/documents/bulk-status/{workflow_id} \
  -H "Authorization: Bearer $TOKEN"
```

## What You Get

✅ Automatic document classification
✅ Parallel processing
✅ Comprehensive synthesis
✅ Cost & risk analysis
✅ Actionable recommendations

## File Locations

- **Agent**: `backend/app/services/langgraph_agent_service.py`
- **Workflow**: `backend/app/workflows/document_workflows.py`
- **API**: `backend/app/api/documents.py` (endpoints 698-968)
- **Frontend**: `frontend/src/components/BulkDocumentUpload.tsx`
- **Migration**: `backend/alembic/versions/b2c3d4e5f6g7_add_langgraph_fields.py`

## Key Commands

```bash
# Generate graph
python scripts/generate_workflow_graph.py

# Start worker
python -m app.workflows.worker

# Run migration
alembic upgrade head

# Check current migration
alembic current

# View logs
tail -f backend/logs/app.log
```

## Endpoints

```
POST   /api/documents/bulk-upload        # Upload multiple files
GET    /api/documents/bulk-status/{id}   # Check processing status
GET    /api/documents/                    # List all documents
GET    /api/documents/{id}                # Get single document
```

## Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'langgraph'`
**Fix**: `pip install langgraph langchain-core`

**Issue**: Documents stuck in "processing"
**Fix**: Make sure worker is running: `python -m app.workflows.worker`

**Issue**: Temporal not connecting
**Fix**: `docker-compose restart temporal`

## Environment Variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
export ENABLE_TEMPORAL_WORKFLOWS=true
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/appartment_agent
```

## Full Guides

- 📖 [Setup Guide](./SETUP_GUIDE.md) - Complete installation
- 📖 [Implementation Guide](./LANGGRAPH_AGENT_IMPLEMENTATION.md) - Architecture
- 📖 [Complete Summary](./IMPLEMENTATION_COMPLETE.md) - What's built

## Success Checklist

- [ ] `pip list | grep langgraph` shows installed packages
- [ ] `docker-compose ps` shows all services running
- [ ] `alembic current` shows migration applied
- [ ] `python scripts/generate_workflow_graph.py` creates graph
- [ ] Worker connects without errors
- [ ] API starts on port 8000
- [ ] Bulk upload returns workflow_id
- [ ] Documents get classified correctly
- [ ] Synthesis is generated

**Ready? Follow the commands above and you're done!** 🎉

Need help? Check the [full setup guide](./SETUP_GUIDE.md).
