"""Run the 50-case benchmark against a running LearnMate backend."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).parent

def call_case(base_url: str, case: dict, timeout: int) -> dict:
    query = urlencode({
        "mode": "study",
        "user_id": f"benchmark_{case['learner_profile']['profile_type']}",
        "profile_json": json.dumps(case["learner_profile"]["dimensions"], ensure_ascii=False),
    })
    url = f"{base_url.rstrip('/')}/api/lecture/{case['course_id']}/{case['lecture_num']}/multi-agent?{query}"
    started = time.perf_counter()
    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return {"case_id": case["case_id"], "ok": True,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "status": payload.get("status"), "verified": payload.get("verified"),
                "version": payload.get("final_version", payload.get("version")),
                "generation_mode": payload.get("generation_mode"),
                "audit_report": payload.get("audit_report"),
                "citations": payload.get("citations", payload.get("sources", [])),
                "resource": payload.get("resource", payload)}
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"case_id": case["case_id"], "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000)}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8002")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    cases = [json.loads(x) for x in (ROOT / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    results = []
    for index, case in enumerate(cases[:args.limit], start=1):
        print(f"[{index}/{min(args.limit, len(cases))}] {case['case_id']}", flush=True)
        results.append(call_case(args.base_url, case, args.timeout))
    (ROOT / "generated_results.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n", encoding="utf-8")
    print(f"saved {len(results)} results to generated_results.jsonl")

if __name__ == "__main__":
    main()
