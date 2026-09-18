#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON:-$ROOT/backend/venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON:-python3}"
fi

echo "== Backend tests =="
cd "$ROOT/backend"
"$PYTHON_BIN" -m pytest tests -q

echo "== Frontend TypeScript =="
cd "$ROOT/frontend"
pnpm exec tsc --noEmit --pretty false

echo "== Frontend Vitest =="
pnpm exec vitest run tests/api/learnmate-client.test.ts

echo "== RAG evaluation =="
cd "$ROOT"
"$PYTHON_BIN" scripts/evaluate_rag.py --min-hit-rate 0.8

echo "== API benchmark =="
"$PYTHON_BIN" scripts/benchmark_services.py --iterations 3

FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
if curl -fsS "$FRONTEND_URL" >/dev/null 2>&1; then
  echo "== Playwright LearnMate smoke =="
  cd "$ROOT/frontend"
  PLAYWRIGHT_BASE_URL="$FRONTEND_URL" pnpm exec playwright test e2e/tests/learnmate-product-smoke.spec.ts --project=chromium
else
  echo "== Playwright LearnMate smoke =="
  echo "Skipped because $FRONTEND_URL is not reachable. Start frontend and rerun with FRONTEND_URL if needed."
fi
