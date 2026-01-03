#!/bin/bash
# AICM Mac Native Development Server
# Starts Backend, Frontend, and Phoenix in parallel
# Per DISC-029: Cross-Platform Development Workflow Strategy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Load environment variables from .env if it exists
if [[ -f .env ]]; then
    # Only export lines that are valid VAR=VALUE assignments (not comments or blank)
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
        # Remove leading/trailing whitespace from key
        key=$(echo "$key" | xargs)
        # Only export if key looks like a valid variable name
        if [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
            export "$key=$value"
        fi
    done < .env
fi

# Port Configuration (from env or defaults)
BACKEND_PORT="${AICM_BACKEND_PORT:-8100}"
FRONTEND_PORT="${AICM_FRONTEND_PORT:-3100}"
PHOENIX_PORT="${AICM_PHOENIX_PORT:-6006}"

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
    lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    lsof -ti:$PHOENIX_PORT | xargs kill -9 2>/dev/null || true
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
check_port $BACKEND_PORT || exit 1
check_port $FRONTEND_PORT || exit 1
check_port $PHOENIX_PORT || exit 1
echo -e "${GREEN}✅ All ports available${NC}"
echo ""

# Start Phoenix (observability)
echo -e "${CYAN}Starting Phoenix (port $PHOENIX_PORT)...${NC}"
PHOENIX_PORT=$PHOENIX_PORT python -m phoenix.server.main serve > /tmp/aicm-phoenix.log 2>&1 &
PID_PHOENIX=$!
PIDS+=($PID_PHOENIX)
sleep 2

if ! kill -0 $PID_PHOENIX 2>/dev/null; then
    echo -e "${RED}❌ Phoenix failed to start. Check /tmp/aicm-phoenix.log${NC}"
else
    echo -e "${GREEN}✅ Phoenix running at http://localhost:$PHOENIX_PORT${NC}"
fi

# Start Backend
echo -e "${CYAN}Starting Backend (port $BACKEND_PORT)...${NC}"
python -m uvicorn backend.main:app --reload --port $BACKEND_PORT > /tmp/aicm-backend.log 2>&1 &
PID_BACKEND=$!
PIDS+=($PID_BACKEND)
sleep 2

if ! kill -0 $PID_BACKEND 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check /tmp/aicm-backend.log${NC}"
else
    echo -e "${GREEN}✅ Backend running at http://localhost:$BACKEND_PORT${NC}"
fi

# Start Frontend
echo -e "${CYAN}Starting Frontend (port $FRONTEND_PORT)...${NC}"
cd frontend
VITE_BACKEND_PORT=$BACKEND_PORT npm run dev > /tmp/aicm-frontend.log 2>&1 &
PID_FRONTEND=$!
PIDS+=($PID_FRONTEND)
cd ..
sleep 3

if ! kill -0 $PID_FRONTEND 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start. Check /tmp/aicm-frontend.log${NC}"
else
    echo -e "${GREEN}✅ Frontend running at http://localhost:$FRONTEND_PORT${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}🚀 All services running!${NC}"
echo ""
echo "  📦 Backend:  http://localhost:$BACKEND_PORT"
echo "  🖥️  Frontend: http://localhost:$FRONTEND_PORT"
echo "  👁️  Phoenix:  http://localhost:$PHOENIX_PORT"
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
