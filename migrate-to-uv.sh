#!/bin/bash
set -e

# ============================================================================
# Migration Script: Pip → UV (10x faster!)
# ============================================================================

echo "🚀 Migrating appartment-agent to UV..."
echo ""

# Colors
GREEN='\033[0.32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}UV not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✓ UV installed${NC}"
else
    echo -e "${GREEN}✓ UV already installed${NC}"
fi

echo ""
echo -e "${BLUE}Step 1: Backing up old environment...${NC}"
cd backend

if [ -d "venv" ]; then
    mv venv venv.old.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Old venv backed up${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Creating new UV virtual environment...${NC}"
uv venv .venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo ""
echo -e "${BLUE}Step 3: Installing dependencies with UV (this is FAST!)...${NC}"
source .venv/bin/activate || . .venv/Scripts/activate
uv pip install -e .
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 4: Installing dev dependencies...${NC}"
uv pip install -e ".[dev]"
echo -e "${GREEN}✓ Dev dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 5: Installing viz dependencies (optional)...${NC}"
if command -v dot &> /dev/null; then
    uv pip install -e ".[viz]" || echo -e "${YELLOW}⚠ Viz dependencies skipped (graphviz not available)${NC}"
else
    echo -e "${YELLOW}⚠ Skipping viz dependencies (install graphviz first: brew install graphviz)${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Verifying installation...${NC}"
python -c "import langgraph; print('✓ LangGraph imported successfully')"
python -c "import langchain_anthropic; print('✓ LangChain imported successfully')"
python -c "import temporalio; print('✓ Temporal imported successfully')"
python -c "import minio; print('✓ MinIO imported successfully')"
echo -e "${GREEN}✓ All imports successful${NC}"

cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Migration complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate the new environment:"
echo -e "   ${BLUE}cd backend && source .venv/bin/activate${NC}"
echo ""
echo "2. Test the graph generation:"
echo -e "   ${BLUE}python scripts/generate_workflow_graph.py${NC}"
echo ""
echo "3. Rebuild Docker images:"
echo -e "   ${BLUE}docker-compose build${NC}"
echo ""
echo "4. Start everything:"
echo -e "   ${BLUE}docker-compose up${NC}"
echo ""
echo "5. Run the migration:"
echo -e "   ${BLUE}docker-compose exec backend alembic upgrade head${NC}"
echo ""
echo "📖 For more details, see: UV_MIGRATION_GUIDE.md"
echo ""
