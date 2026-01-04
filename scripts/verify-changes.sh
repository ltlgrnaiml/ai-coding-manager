#!/bin/bash
# AICM Post-Change Verification Script
# Run after ANY code changes to prevent .env and database loading failures
#
# Usage: ./scripts/verify-changes.sh [--quick]
#   --quick: Skip container rebuild (for fast checks only)

set -e

QUICK_MODE=false
if [ "$1" = "--quick" ]; then
    QUICK_MODE=true
fi

echo "🔍 AICM Post-Change Verification"
echo "================================"
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() { echo -e "${GREEN}✅${NC} $1"; }
fail() { echo -e "${RED}❌${NC} $1"; ((ERRORS++)); }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; ((WARNINGS++)); }

# =============================================================================
# 1. Environment File Checks
# =============================================================================
echo "1️⃣  Environment File Checks"
echo "----------------------------"

# Check .env exists
if [ -f .env ]; then
    pass ".env file exists"
else
    fail ".env file missing - copy from .env.example"
fi

# Check for placeholder API keys
if [ -f .env ]; then
    if grep -q "XAI_API_KEY=your-api-key-here" .env 2>/dev/null; then
        fail "XAI_API_KEY still has placeholder value"
    elif grep -q "XAI_API_KEY=.\+" .env 2>/dev/null; then
        pass "XAI_API_KEY is configured"
    else
        warn "XAI_API_KEY may not be set"
    fi
fi

# Check .env.example exists (for reference)
if [ -f .env.example ]; then
    pass ".env.example exists"
else
    warn ".env.example missing"
fi

echo ""

# =============================================================================
# 2. Docker Container Checks
# =============================================================================
echo "2️⃣  Docker Container Checks"
echo "----------------------------"

# Check Docker is running
if docker info > /dev/null 2>&1; then
    pass "Docker daemon running"
else
    fail "Docker daemon not running"
    echo "   Run: docker desktop or systemctl start docker"
    exit 1
fi

# Rebuild containers (unless quick mode)
if [ "$QUICK_MODE" = false ]; then
    echo "   Rebuilding containers..."
    if docker compose build backend frontend --quiet 2>/dev/null; then
        pass "Containers rebuilt successfully"
    else
        fail "Container build failed"
    fi
    
    # Restart services
    echo "   Restarting services..."
    if docker compose up -d --quiet-pull 2>/dev/null; then
        pass "Services restarted"
        sleep 3  # Wait for startup
    else
        fail "Failed to start services"
    fi
else
    echo "   (Skipping rebuild in quick mode)"
fi

# Check containers are running
BACKEND_STATUS=$(docker compose ps backend --format "{{.Status}}" 2>/dev/null | head -1)
if [[ "$BACKEND_STATUS" == *"Up"* ]]; then
    pass "Backend container running"
else
    fail "Backend container not running"
fi

FRONTEND_STATUS=$(docker compose ps frontend --format "{{.Status}}" 2>/dev/null | head -1)
if [[ "$FRONTEND_STATUS" == *"Up"* ]]; then
    pass "Frontend container running"
else
    fail "Frontend container not running"
fi

echo ""

# =============================================================================
# 3. Database Initialization Checks
# =============================================================================
echo "3️⃣  Database Initialization Checks"
echo "-----------------------------------"

# Check database initialization in logs
LOGS=$(docker compose logs backend 2>&1 | tail -100)

if echo "$LOGS" | grep -q "SQLite knowledge database initialized"; then
    pass "Knowledge database initialized"
else
    fail "Knowledge database NOT initialized"
fi

if echo "$LOGS" | grep -q "P2RE trace database initialized"; then
    pass "P2RE database initialized"
else
    fail "P2RE database NOT initialized"
fi

if echo "$LOGS" | grep -q "Memory database initialized"; then
    pass "Memory database initialized"
else
    fail "Memory database NOT initialized"
fi

# Check for initialization errors
if echo "$LOGS" | grep -q "Failed to initialize"; then
    fail "Database initialization errors found"
    echo "   Check: docker compose logs backend | grep -i 'failed'"
fi

echo ""

# =============================================================================
# 4. API Health Checks
# =============================================================================
echo "4️⃣  API Health Checks"
echo "---------------------"

# Backend health
HEALTH=$(curl -sf http://localhost:8100/api/health 2>/dev/null)
if [ $? -eq 0 ]; then
    if echo "$HEALTH" | grep -q '"status":"healthy"'; then
        pass "Backend API healthy"
    else
        warn "Backend API returned unexpected response"
    fi
else
    fail "Backend API unreachable at localhost:8100"
fi

# Frontend
if curl -sf http://localhost:3100 > /dev/null 2>&1; then
    pass "Frontend accessible at localhost:3100"
else
    fail "Frontend unreachable at localhost:3100"
fi

# Phoenix (optional)
if curl -sf http://localhost:6006 > /dev/null 2>&1; then
    pass "Phoenix UI accessible at localhost:6006"
else
    warn "Phoenix UI not running (optional)"
fi

echo ""

# =============================================================================
# 5. Database File Checks
# =============================================================================
echo "5️⃣  Database File Checks"
echo "------------------------"

DB_DIR="$HOME/.aikh"

if [ -d "$DB_DIR" ]; then
    pass "Database directory exists: $DB_DIR"
else
    warn "Database directory missing: $DB_DIR"
fi

for db in knowledge.db p2re.db memory.db; do
    if [ -f "$DB_DIR/$db" ]; then
        SIZE=$(ls -lh "$DB_DIR/$db" 2>/dev/null | awk '{print $5}')
        pass "$db exists ($SIZE)"
    else
        warn "$db not found"
    fi
done

echo ""

# =============================================================================
# Summary
# =============================================================================
echo "================================"
echo "           SUMMARY"
echo "================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s), but no errors${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Missing .env: cp .env.example .env && edit"
    echo "  - Container issues: docker compose down && docker compose up -d"
    echo "  - Database issues: Check logs with: docker compose logs backend"
    exit 1
fi
