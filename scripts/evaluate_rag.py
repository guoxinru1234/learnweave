#!/usr/bin/env python3
"""Evaluate RAG retrieval against course-specific acceptance queries."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.rag.engine import RAGEngine  # noqa: E402


EVAL_CASES = [
    {
        "query": "Spark on YARN 部署",
        "expected": ["YARN", "部署", "Spark"],
    },
    {
        "query": "DataFrame 创建",
        "expected": ["DataFrame", "Spark SQL"],
    },
    {
        "query": "Scala 函数式编程习题",
        "expected": ["Scala", "函数"],
    },
    {
        "query": "RDD 编程实战",
        "expected": ["RDD", "编程"],
    },
    {
        "query": "Shuffle 性能优化",
        "expected": ["Shuffle", "reduceByKey"],
    },
]


def _haystack(result: dict) -> str:
    return " ".join(
        str(value)
        for value in [
            result.get("title", ""),
            result.get("category", ""),
            result.get("source_path", ""),
            " ".join(result.get("topics", []) or []),
            result.get("preview", ""),
            result.get("snippet", ""),
            result.get("text", ""),
            result.get("content", ""),
        ]
    ).lower()


def evaluate(top_k: int) -> dict:
    engine = RAGEngine(str(ROOT / "knowledge-base"))
    rows = []
    hits = 0
    for case in EVAL_CASES:
        results = engine.search(case["query"], top_k=top_k)
        haystacks = [_haystack(result) for result in results]
        matched_terms = [
            term for term in case["expected"]
            if any(term.lower() in haystack for haystack in haystacks)
        ]
        passed = len(matched_terms) >= 1
        hits += int(passed)
        rows.append({
            "query": case["query"],
            "expected": case["expected"],
            "matched_terms": matched_terms,
            "passed": passed,
            "top_titles": [result.get("title") for result in results[:3]],
        })
    return {
        "total": len(EVAL_CASES),
        "hits": hits,
        "hit_rate": round(hits / len(EVAL_CASES), 3),
        "top_k": top_k,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-hit-rate", type=float, default=0.8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = evaluate(args.top_k)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"RAG hit rate: {report['hits']}/{report['total']} = {report['hit_rate']}")
        for row in report["cases"]:
            marker = "PASS" if row["passed"] else "FAIL"
            print(f"[{marker}] {row['query']} -> {', '.join(row['top_titles'] or [])}")

    if report["hit_rate"] < args.min_hit_rate:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
