#!/bin/bash
# AICM Mac Native Development Server
# Starts Backend, Frontend, and Phoenix in parallel
# Per DISC-029: Cross-Platform Development Workflow Strategy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}🍎 AICM Mac Native Development Server${NC}"
echo "========================================"
echo ""

# Check if we're in a venv
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  No venv active. Activating .venv...${NC}"
    source .venv/bin/activate
fi

# Store PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Kill any remaining processes on our ports
    lsof -ti:8100 | xargs kill -9 2>/dev/null || true
    lsof -ti:3100 | xargs kill -9 2>/dev/null || true
    lsof -ti:6006 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check for port conflicts
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        echo "   Run: lsof -i :$1 to see what's using it"
        return 1
    fi
    return 0
}

echo -e "${CYAN}Checking ports...${NC}"
check_port 8100 || exit 1
check_port 3100 || exit 1
check_port 6006 || exit 1
echo -e "${GREEN}✅ All ports available${NC}"
echo ""

# Start Phoenix (observability)
echo -e "${CYAN}Starting Phoenix (port 6006)...${NC}"
PHOENIX_PORT=6006 python -m phoenix.server.main serve > /tmp/aicm-phoenix.log 2>&1 &
PID_PHOENIX=$!
PIDS+=($PID_PHOENIX)
sleep 2

if ! kill -0 $PID_PHOENIX 2>/dev/null; then
    echo -e "${RED}❌ Phoenix failed to start. Check /tmp/aicm-phoenix.log${NC}"
else
    echo -e "${GREEN}✅ Phoenix running at http://localhost:6006${NC}"
fi

# Start Backend
echo -e "${CYAN}Starting Backend (port 8100)...${NC}"
python -m uvicorn backend.main:app --reload --port 8100 > /tmp/aicm-backend.log 2>&1 &
PID_BACKEND=$!
PIDS+=($PID_BACKEND)
sleep 2

if ! kill -0 $PID_BACKEND 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check /tmp/aicm-backend.log${NC}"
else
    echo -e "${GREEN}✅ Backend running at http://localhost:8100${NC}"
fi

# Start Frontend
echo -e "${CYAN}Starting Frontend (port 3100)...${NC}"
cd frontend
npm run dev > /tmp/aicm-frontend.log 2>&1 &
PID_FRONTEND=$!
PIDS+=($PID_FRONTEND)
cd ..
sleep 3

if ! kill -0 $PID_FRONTEND 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start. Check /tmp/aicm-frontend.log${NC}"
else
    echo -e "${GREEN}✅ Frontend running at http://localhost:3100${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}🚀 All services running!${NC}"
echo ""
echo "  📦 Backend:  http://localhost:8100"
echo "  🖥️  Frontend: http://localhost:3100"
echo "  👁️  Phoenix:  http://localhost:6006"
echo ""
echo "  📋 Logs:"
echo "     tail -f /tmp/aicm-backend.log"
echo "     tail -f /tmp/aicm-frontend.log"
echo "     tail -f /tmp/aicm-phoenix.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo "========================================"

# Wait for all processes
wait
