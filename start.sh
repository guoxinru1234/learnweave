#!/bin/bash
# ============================================================
# LearnMate local startup script
# Usage: ./start.sh [--backend-only|--frontend-only|--restart|--stop|--status|--help]
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}"
LOG_DIR="$ROOT/logs"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'

usage() {
    cat <<EOF
LearnMate local startup script

Usage:
  ./start.sh                 Start backend and frontend, replacing listeners on ${BACKEND_PORT}/${FRONTEND_PORT}
  ./start.sh --backend-only  Start only FastAPI backend
  ./start.sh --frontend-only Start only Next.js frontend
  ./start.sh --restart       Stop both services, then start both
  ./start.sh --stop          Stop services on configured ports
  ./start.sh --status        Show local service status
  ./start.sh --help          Show this help

Environment overrides:
  BACKEND_PORT=8001 FRONTEND_PORT=3001 NEXT_PUBLIC_API_URL=http://localhost:8001 ./start.sh
EOF
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "${RED}[Error]${NC} Missing command: $1"
        exit 1
    fi
}

port_pids() {
    lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true
}

stop_port() {
    local label="$1"
    local port="$2"
    local pids
    pids="$(port_pids "$port")"

    if [ -z "$pids" ]; then
        echo -e "${YELLOW}[$label]${NC} No listener on port $port"
        return
    fi

    echo "$pids" | while read -r pid; do
        [ -z "$pid" ] && continue
        kill "$pid" 2>/dev/null || true
    done
    sleep 1
    echo -e "${GREEN}[$label]${NC} Stopped port $port"
}

stop_services() {
    stop_port "Backend" "$BACKEND_PORT"
    stop_port "Frontend" "$FRONTEND_PORT"
}

wait_for_url() {
    local url="$1"
    local attempts="${2:-30}"

    for _ in $(seq 1 "$attempts"); do
        if curl -fsS "$url" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

status_url() {
    local label="$1"
    local url="$2"

    if curl -fsS "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}[$label]${NC} running: $url"
    else
        echo -e "${YELLOW}[$label]${NC} not responding: $url"
    fi
}

status_services() {
    status_url "Backend" "http://localhost:${BACKEND_PORT}/health"
    status_url "Frontend" "http://localhost:${FRONTEND_PORT}"
    echo "API docs: http://localhost:${BACKEND_PORT}/docs"
}

start_backend() {
    require_command curl
    require_command lsof

    if [ ! -x "$ROOT/backend/venv/bin/python" ]; then
        echo -e "${RED}[Backend]${NC} Missing backend virtualenv: backend/venv"
        echo "Run make all, or create backend/venv and install backend/requirements.txt."
        exit 1
    fi

    mkdir -p "$LOG_DIR"
    stop_port "Backend" "$BACKEND_PORT"

    echo -e "${BLUE}[Backend]${NC} Starting FastAPI on port $BACKEND_PORT..."
    (
        cd "$ROOT/backend"
        source venv/bin/activate
        nohup uvicorn app.main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT" \
            > "$LOG_DIR/backend.log" 2>&1 &
        echo $! > "$LOG_DIR/backend.pid"
    )

    if wait_for_url "http://localhost:${BACKEND_PORT}/health" 30; then
        echo -e "${GREEN}[Backend]${NC} http://localhost:$BACKEND_PORT"
    else
        echo -e "${RED}[Backend]${NC} Startup failed. See $LOG_DIR/backend.log"
        exit 1
    fi
}

start_frontend() {
    require_command curl
    require_command lsof
    require_command pnpm

    if [ ! -d "$ROOT/frontend/node_modules" ]; then
        echo -e "${RED}[Frontend]${NC} Missing frontend/node_modules"
        echo "Run make all, or run pnpm install in frontend/."
        exit 1
    fi

    mkdir -p "$LOG_DIR"
    stop_port "Frontend" "$FRONTEND_PORT"

    echo -e "${BLUE}[Frontend]${NC} Starting Next.js on port $FRONTEND_PORT..."
    (
        cd "$ROOT/frontend"
        nohup env NEXT_PUBLIC_API_URL="$API_URL" pnpm dev --port "$FRONTEND_PORT" \
            > "$LOG_DIR/frontend.log" 2>&1 &
        echo $! > "$LOG_DIR/frontend.pid"
    )

    if wait_for_url "http://localhost:${FRONTEND_PORT}" 45; then
        echo -e "${GREEN}[Frontend]${NC} http://localhost:$FRONTEND_PORT"
    else
        echo -e "${RED}[Frontend]${NC} Startup failed. See $LOG_DIR/frontend.log"
        exit 1
    fi
}

echo "========================================"
echo "  LearnMate Local Startup"
echo "========================================"

case "${1:-}" in
    --backend-only)
        start_backend
        ;;
    --frontend-only)
        start_frontend
        ;;
    --restart|"")
        stop_services
        start_backend
        start_frontend
        ;;
    --stop)
        stop_services
        exit 0
        ;;
    --status)
        status_services
        exit 0
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        usage
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  Backend:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  API docs: ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  Logs:     ${GREEN}$LOG_DIR${NC}"
echo -e "${GREEN}========================================${NC}"
