from fastapi import Depends
from ..core.deps import get_current_user_id
"""Assessment routes — 基于真实画像数据"""
from fastapi import APIRouter
from ..models.profile import get_profile, DIMENSION_LABELS, DIMENSION_KEYS
from ..agents.assessment_agent import get_assessment_agent
from ..core.database import get_connection

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("/summary")
async def assessment_summary(user_id: int = Depends(get_current_user_id)):
    """返回基于用户真实画像+随学随新的学习评估"""
    profile = get_profile(user_id)
    agent = get_assessment_agent()

    # 直接用画像原始分数（与学情画像一致，不加学习行为加分）
    # Assessment must mirror the ten-dimensional domain profile used by the
    # profile and learning-space pages (not the legacy six-field model).
    score_keys = list(profile.domain_skills.keys()) if profile.domain_skills else list(DIMENSION_KEYS)
    profile_scores = [int(profile.domain_skills.get(k, 0)) for k in score_keys]

    # 调用评估 Agent
    result = agent.assess(profile_scores)

    # 直接用画像的薄弱维度
    weak_points = [
        {"name": name, "score": score, "action": f"建议重点学习{name}相关课程内容"}
        for name, score in profile.weak_dimensions
    ]

    color_map = lambda v: "#16a34a" if v >= 80 else "#2563eb" if v >= 70 else "#d97706" if v >= 60 else "#dc2626"

    knowledge = []
    for i, key in enumerate(score_keys):
        val = profile_scores[i] if i < len(profile_scores) else 0
        knowledge.append({
            "name": DIMENSION_LABELS.get(key, key),
            "val": val,
            "color": color_map(val),
        })
    overall = sum(profile_scores) // len(profile_scores) if profile_scores else 0
    conn = get_connection()
    quiz_rows = conn.execute("SELECT topic, score, total, created_at FROM quiz_attempts WHERE learner_id=? ORDER BY created_at DESC", (str(user_id),)).fetchall()
    conn.close()
    quiz_records = [{"topic": r[0] or "综合练习", "score": int(r[1] or 0), "total": int(r[2] or 1), "created_at": r[3]} for r in quiz_rows]
    quiz_total = sum(r["total"] for r in quiz_records)
    quiz_correct = sum(r["score"] for r in quiz_records)

    # 知识点掌握度（从 assessment_agent 的 SQLite 数据获取）
    topic_mastery = []
    for topic, score in agent.mastery_data.items():
        val = int(score * 100)
        topic_mastery.append({
            "name": topic,
            "val": val,
            "color": color_map(val),
        })

    return {
        "overall": overall,
        "mastery": overall,
        "experiment_mastery": result.get("experiment_mastery", 0),
        "weak_points": weak_points,
        "recommendations": result["recommendations"],
        "knowledge": knowledge,
        "topic_mastery": topic_mastery,
        "quiz_records": quiz_records,
        "quiz_attempts": len(quiz_records),
        "quiz_accuracy": round(quiz_correct / quiz_total * 100) if quiz_total else 0,
        "profile_based": True,
    }
