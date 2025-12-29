#!/bin/bash
set -e

# ============================================================================
# Migration Script: npm → PNPM (10x faster!)
# ============================================================================

echo "🚀 Migrating frontend to PNPM..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo -e "${YELLOW}PNPM not found. Installing...${NC}"
    npm install -g pnpm@8
    echo -e "${GREEN}✓ PNPM installed${NC}"
else
    echo -e "${GREEN}✓ PNPM already installed ($(pnpm --version))${NC}"
fi

echo ""
echo -e "${BLUE}Step 1: Backing up old files...${NC}"
cd frontend

# Backup old node_modules and lock files
if [ -d "node_modules" ]; then
    mv node_modules node_modules.old.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Old node_modules backed up${NC}"
fi

if [ -f "package-lock.json" ]; then
    mv package-lock.json package-lock.json.old.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✓ Old package-lock.json backed up${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Installing dependencies with PNPM (this is FAST!)...${NC}"
pnpm install
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 3: Verifying installation...${NC}"
pnpm list react next axios --depth=0
echo -e "${GREEN}✓ Key packages verified${NC}"

cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✨ Frontend migration complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the development server:"
echo -e "   ${BLUE}cd frontend && pnpm dev${NC}"
echo ""
echo "2. Rebuild Docker images with PNPM:"
echo -e "   ${BLUE}docker-compose build frontend${NC}"
echo ""
echo "3. Start the full stack:"
echo -e "   ${BLUE}docker-compose up${NC}"
echo ""
echo "Key PNPM commands (replace 'npm' with 'pnpm'):"
echo -e "   ${BLUE}pnpm install${NC}           - Install all dependencies"
echo -e "   ${BLUE}pnpm add <package>${NC}     - Add a new package"
echo -e "   ${BLUE}pnpm remove <package>${NC}  - Remove a package"
echo -e "   ${BLUE}pnpm dev${NC}               - Start dev server"
echo -e "   ${BLUE}pnpm build${NC}             - Build for production"
echo -e "   ${BLUE}pnpm start${NC}             - Start production server"
echo ""
echo "📖 For more details, see: FRONTEND_MIGRATION_GUIDE.md"
echo ""
