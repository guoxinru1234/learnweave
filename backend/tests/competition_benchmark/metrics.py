"""Summarize benchmark execution without inventing missing measurements."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent

def main() -> None:
    cases = [json.loads(x) for x in (ROOT / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    path = ROOT / "generated_results.jsonl"
    if not path.exists():
        raise SystemExit("generated_results.jsonl does not exist; run run_benchmark.py first")
    results = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line); results[item["case_id"]] = item
    completed = [results[c["case_id"]] for c in cases if results.get(c["case_id"], {}).get("ok")]
    approved = [r for r in completed if r.get("status") == "approved" or r.get("verified") is True]
    cited = [r for r in completed if r.get("citations")]
    scores = [r["audit_report"].get("difficulty_match_score") for r in completed
              if isinstance(r.get("audit_report"), dict)
              and isinstance(r["audit_report"].get("difficulty_match_score"), (int, float))]
    summary = {
        "total_cases": len(cases), "completed_cases": len(completed),
        "failed_requests": len(cases) - len(completed), "approved_cases": len(approved),
        "approval_rate": round(len(approved) / len(cases) * 100, 2) if cases else 0,
        "cases_with_citations": len(cited),
        "citation_rate": round(len(cited) / len(cases) * 100, 2) if cases else 0,
        "difficulty_scores_observed": len(scores),
        "difficulty_average": round(sum(scores) / len(scores), 2) if scores else None,
        "measurement_status": "partial" if len(completed) < len(cases) or not scores else "requires_fact_and_code_audit",
    }
    (ROOT / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
