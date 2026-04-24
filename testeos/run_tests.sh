#!/bin/bash
# Script para ejecutar los tests RAGAS de manera fácil

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🧪 RAGAS Test Suite - Vodafone RAG API${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Check if API is running
echo -e "\n${YELLOW}📋 Checking if API is running on port 5001...${NC}"
if ! curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${RED}❌ API is not running on port 5001!${NC}"
    echo -e "${YELLOW}Please start the API with:${NC}"
    echo -e "  ${BLUE}sudo systemctl start rag-vodafone${NC}"
    echo -e "Or manually:${NC}"
    echo -e "  ${BLUE}cd /home/administrador/vodafone${NC}"
    echo -e "  ${BLUE}python -m uvicorn api:app --host 0.0.0.0 --port 5001${NC}"
    exit 1
fi
echo -e "${GREEN}✅ API is running on port 5001${NC}"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Run simple test
echo -e "\n${YELLOW}📞 Running tests...${NC}"
cd "$SCRIPT_DIR"

if python simple_test.py; then
    echo -e "\n${GREEN}✅ Tests completed successfully!${NC}"
    
    # Show summary
    echo -e "\n${YELLOW}📊 Viewing results...${NC}"
    python view_results.py
else
    echo -e "\n${RED}❌ Tests failed!${NC}"
    exit 1
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Test suite execution complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
