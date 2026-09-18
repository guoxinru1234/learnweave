"""验证编排API — 赛题B：生成→审核→修正→复审→决策"""
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/verification", tags=["verification"])


class VerificationRequest(BaseModel):
    course_id: str = "python-data-analysis"
    lecture_num: int = 1
    course_title: str = "Python数据分析实战"
    lecture_topic: str = ""
    profile: dict = None
    mode: str = "study"


@router.post("/generate")
async def generate_with_verification(req: VerificationRequest):
    """
    赛题B核心端点：完整验证闭环生成资源

    流程：生成(5 Agent并行) → 审核(AuditAgent交叉验证)
         → 修正(LLM根据审核意见修正) → 复审(重新审核)
         → 决策(输出最终结果+置信度报告)

    区别于赛题A：不只生成资源，还要交叉验证确保准确性
    """
    from ..agents.verification_orchestrator import get_verification_orchestrator

    orch = get_verification_orchestrator()
    result = await orch.run(
        course_id=req.course_id,
        lecture_num=req.lecture_num,
        course_title=req.course_title,
        lecture_topic=req.lecture_topic or f"第{req.lecture_num}讲",
        profile=req.profile,
        mode=req.mode,
    )
    return result


@router.get("/audit-report/{course_id}/{lecture_num}")
async def get_audit_report(course_id: str, lecture_num: int):
    """获取指定讲次的审核报告（如果已生成）"""
    import json, os
    cache_file = f"data/audit_cache/{course_id}_{lecture_num}.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"message": "暂无审核报告", "verified": False}


@router.get("/status")
async def verification_status():
    return {
        "orchestrator": "VerificationOrchestrator (生成→审核→修正→复审→决策)",
        "agents": [
            {"id": "audit", "name": "内容审核Agent", "role": "交叉验证准确性,检测幻觉"},
            {"id": "fix", "name": "内容修正Agent", "role": "根据审核意见修正错误"},
            {"id": "doc", "name": "文档生成Agent", "role": "生成讲义"},
            {"id": "mindmap", "name": "导图生成Agent", "role": "生成思维导图"},
            {"id": "code", "name": "代码生成Agent", "role": "生成代码案例"},
            {"id": "reading", "name": "阅读推荐Agent", "role": "生成拓展阅读"},
        ],
        "pipeline": ["生成", "审核", "修正", "复审", "决策"],
    }
