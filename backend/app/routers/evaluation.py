"""Quality evaluation API — exposes offline evaluation metrics."""
import json, os
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])
REPORT_PATH = Path(__file__).parent.parent.parent / "tests" / "eval_report.json"


@router.get("/report")
def get_evaluation_report():
    """返回离线评测报告（如果存在）"""
    if REPORT_PATH.exists():
        try:
            with open(REPORT_PATH, encoding="utf-8") as f:
                data = json.load(f)
            return {"available": True, "report": data}
        except Exception:
            pass
    return {
        "available": False,
        "message": "暂无质量评测数据。请运行 backend/tests/offline_eval.py 生成报告。",
        "suggested_command": "cd backend/tests && python offline_eval.py",
    }


@router.get("/status")
def get_evaluation_status():
    """快速检查评测数据是否可用"""
    return {"available": REPORT_PATH.exists(), "report_path": str(REPORT_PATH)}
