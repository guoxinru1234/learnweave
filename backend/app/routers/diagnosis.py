"""学情诊断报告 API"""
from fastapi import APIRouter, HTTPException
from ..agents.diagnosis_report import generate_report

router = APIRouter(prefix="/api/learners", tags=["diagnosis"])


@router.get("/{learner_id}/diagnosis-report")
def get_diagnosis_report(learner_id: int):
    """获取学习者完整学情诊断报告。

    返回: knowledge_mastery, knowledge_gaps, mastered_points,
          resource_match, learning_path, recent_feedback,
          difficulty_history, decision_history.
    """
    if learner_id <= 0:
        raise HTTPException(400, "Invalid learner_id")
    return generate_report(learner_id)
