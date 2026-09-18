"""学习交互反馈路由"""
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from ..agents.feedback_agent import get_feedback_agent

router = APIRouter(prefix="/api/learning", tags=["learning"])


class InteractionRequest(BaseModel):
    learner_id: int
    resource_id: str = ""
    question_id: str = ""
    answer: str = ""
    is_correct: bool = False
    attempt_count: int = 1
    time_spent_seconds: int = 0
    hint_used: bool = False
    topic: str = ""

    @field_validator("learner_id")
    @classmethod
    def validate_learner(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("learner_id must be positive")
        return v


@router.post("/interactions")
def submit_interaction(req: InteractionRequest):
    """提交学习交互，返回掌握度更新和动态决策"""
    agent = get_feedback_agent()
    result = agent.process(
        learner_id=req.learner_id,
        resource_id=req.resource_id,
        question_id=req.question_id,
        answer=req.answer,
        is_correct=req.is_correct,
        attempt_count=req.attempt_count,
        time_spent_seconds=req.time_spent_seconds,
        hint_used=req.hint_used,
        topic=req.topic,
    )
    return result
