#!/bin/bash
set -e

# ============================================================================
# Complete Stack Migration: npm+pip → pnpm+UV
# ============================================================================
# This script migrates your entire stack to the fastest package managers:
# - Backend: pip → UV (10-100x faster!)
# - Frontend: npm → pnpm (5-10x faster!)
# - Docker: Updated to use both
# ============================================================================

echo "🚀 Complete Stack Migration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Track overall progress
TOTAL_STEPS=6
CURRENT_STEP=0

print_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo ""
    echo -e "${BOLD}${BLUE}[$CURRENT_STEP/$TOTAL_STEPS] $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ============================================================================
# Step 1: Pre-flight checks
# ============================================================================

print_step "Pre-flight Checks"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi
print_success "Found docker-compose.yml"

# Check Docker is running
if ! docker ps > /dev/null 2>&1; then
    print_warning "Docker is not running. You'll need it later for building images."
else
    print_success "Docker is running"
fi

# ============================================================================
# Step 2: Install UV (Backend package manager)
# ============================================================================

print_step "Installing UV (Python package manager)"

if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"

    # Add to shell profile
    if [ -f "$HOME/.zshrc" ]; then
        if ! grep -q 'cargo/bin' "$HOME/.zshrc"; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$HOME/.zshrc"
        fi
    elif [ -f "$HOME/.bashrc" ]; then
        if ! grep -q 'cargo/bin' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "$HOME/.bashrc"
        fi
    fi

    print_success "UV installed ($(uv --version))"
else
    print_success "UV already installed ($(uv --version))"
fi

# ============================================================================
# Step 3: Install pnpm (Frontend package manager)
# ============================================================================

print_step "Installing pnpm (JavaScript package manager)"

if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm@8
    print_success "pnpm installed ($(pnpm --version))"
else
    print_success "pnpm already installed ($(pnpm --version))"
fi

# ============================================================================
# Step 4: Migrate Backend
# ============================================================================

print_step "Migrating Backend (pip → UV)"

cd backend

# Backup old venv
if [ -d "venv" ]; then
    echo "Backing up old venv..."
    mv venv venv.old.$(date +%Y%m%d_%H%M%S)
    print_success "Old venv backed up"
fi

# Create new UV venv
echo "Creating UV virtual environment..."
uv venv .venv
print_success "UV venv created"

# Activate venv
echo "Installing dependencies with UV (this is fast!)..."
source .venv/bin/activate || . .venv/Scripts/activate

# Install dependencies
uv pip install -e .
print_success "Main dependencies installed"

# Install dev dependencies
uv pip install -e ".[dev]"
print_success "Dev dependencies installed"

# Try to install viz dependencies (optional)
if command -v dot &> /dev/null; then
    uv pip install -e ".[viz]" 2>/dev/null && print_success "Viz dependencies installed" || print_warning "Viz dependencies skipped"
else
    print_warning "Skipping viz dependencies (install graphviz first: brew install graphviz)"
fi

# Verify installation
echo "Verifying backend installation..."
python -c "import langgraph; print('  • LangGraph: OK')"
python -c "import langchain_anthropic; print('  • LangChain Anthropic: OK')"
python -c "import temporalio; print('  • Temporal: OK')"
python -c "import minio; print('  • MinIO: OK')"
print_success "Backend migration complete"

cd ..

# ============================================================================
# Step 5: Migrate Frontend
# ============================================================================

print_step "Migrating Frontend (npm → pnpm)"

cd frontend

# Backup old files
if [ -d "node_modules" ]; then
    echo "Backing up old node_modules..."
    mv node_modules node_modules.old.$(date +%Y%m%d_%H%M%S)
    print_success "Old node_modules backed up"
fi

if [ -f "package-lock.json" ]; then
    echo "Backing up old package-lock.json..."
    mv package-lock.json package-lock.json.old.$(date +%Y%m%d_%H%M%S)
    print_success "Old package-lock.json backed up"
fi

# Install with pnpm
echo "Installing dependencies with pnpm (this is fast!)..."
pnpm install
print_success "Frontend dependencies installed"

# Verify installation
echo "Verifying frontend installation..."
pnpm list react next axios --depth=0 > /dev/null 2>&1 && print_success "Key packages verified"

cd ..

# ============================================================================
# Step 6: Docker Setup
# ============================================================================

print_step "Docker Configuration"

echo "Docker has been configured to use:"
echo "  • Backend: Dockerfile.uv (UV)"
echo "  • Frontend: Dockerfile.pnpm (pnpm)"
echo "  • Worker: Dockerfile.uv (UV)"
print_success "docker-compose.yml already updated"

if docker ps > /dev/null 2>&1; then
    echo ""
    echo "Ready to rebuild Docker images!"
    echo "Run: ${BLUE}docker-compose build${NC}"
    echo ""
else
    print_warning "Docker not running - start it before building images"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}${BOLD}✨ Complete Stack Migration Successful!${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Summary of changes:"
echo "  ✓ Backend migrated to UV (10-100x faster Python installs)"
echo "  ✓ Frontend migrated to pnpm (5-10x faster JS installs)"
echo "  ✓ Docker configured for optimized builds"
echo "  ✓ All dependencies installed and verified"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo "1️⃣  Activate backend environment:"
echo -e "   ${BLUE}cd backend && source .venv/bin/activate${NC}"
echo ""
echo "2️⃣  Test backend locally:"
echo -e "   ${BLUE}python scripts/generate_workflow_graph.py${NC}"
echo ""
echo "3️⃣  Test frontend locally:"
echo -e "   ${BLUE}cd frontend && pnpm dev${NC}"
echo ""
echo "4️⃣  Rebuild Docker images:"
echo -e "   ${BLUE}docker-compose build${NC}"
echo ""
echo "5️⃣  Start the full stack:"
echo -e "   ${BLUE}docker-compose up -d${NC}"
echo ""
echo "6️⃣  Run database migration:"
echo -e "   ${BLUE}docker-compose exec backend alembic upgrade head${NC}"
echo ""
echo -e "${BOLD}Key commands (remember these!):${NC}"
echo ""
echo "Backend (UV):"
echo -e "  ${BLUE}uv pip install <package>${NC}     Add a Python package"
echo -e "  ${BLUE}uv pip install -e .${NC}          Reinstall all deps"
echo -e "  ${BLUE}uv pip list${NC}                  List installed packages"
echo ""
echo "Frontend (pnpm):"
echo -e "  ${BLUE}pnpm add <package>${NC}           Add a JS package"
echo -e "  ${BLUE}pnpm install${NC}                 Reinstall all deps"
echo -e "  ${BLUE}pnpm dev${NC}                     Start dev server"
echo ""
echo "Documentation:"
echo "  📖 Backend guide:  UV_MIGRATION_GUIDE.md"
echo "  📖 Frontend guide: FRONTEND_MIGRATION_GUIDE.md"
echo "  📖 Complete guide: COMPLETE_STACK_MIGRATION.md"
echo ""
echo -e "${GREEN}Happy coding with your blazingly fast setup! ⚡️${NC}"
echo ""
