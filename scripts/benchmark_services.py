#!/usr/bin/env python3
"""Benchmark local API routes through FastAPI TestClient."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


REQUESTS = [
    ("GET", "/health", None),
    ("GET", "/api/knowledge/search?q=DataFrame", None),
    ("GET", "/api/labs", None),
    ("POST", "/api/generate/resource", {"topic": "DataFrame 创建"}),
    ("POST", "/api/generate/quiz", {"topic": "RDD 编程实战", "count": 3}),
    ("POST", "/api/generate/tutor", {"topic": "DataFrame 创建", "question": "实验前需要检查什么？"}),
    ("POST", "/api/agents/run", {"profile": [72, 80, 55, 75, 90, 85]}),
]


def run(iterations: int) -> dict:
    client = TestClient(app)
    rows = []
    for method, path, payload in REQUESTS:
        durations = []
        status_codes = []
        for _ in range(iterations):
            start = time.perf_counter()
            response = client.request(method, path, json=payload)
            durations.append((time.perf_counter() - start) * 1000)
            status_codes.append(response.status_code)
        rows.append({
            "method": method,
            "path": path,
            "status_codes": status_codes,
            "p50_ms": round(statistics.median(durations), 2),
            "max_ms": round(max(durations), 2),
            "ok": all(code < 400 for code in status_codes),
        })
    return {"iterations": iterations, "routes": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(args.iterations)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in report["routes"]:
            marker = "PASS" if row["ok"] else "FAIL"
            print(f"[{marker}] {row['method']} {row['path']} p50={row['p50_ms']}ms max={row['max_ms']}ms")
    return 0 if all(row["ok"] for row in report["routes"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
