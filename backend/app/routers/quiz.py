from fastapi import Depends
from ..core.deps import get_current_user_id
"""Quiz routes."""
from typing import Optional
import json
from fastapi import APIRouter
from pydantic import BaseModel
from ..core.database import get_connection
from ..core.event_bus import event_bus
from ..services.quiz_bank import recommendation_questions

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class QuizSubmitRequest(BaseModel):
    topic: str = ""
    score: int = 0
    total: int = 10


@router.get("/recommend")
async def recommend_quiz(topic: Optional[str] = None):
    return recommendation_questions(topic)

@router.get("/progress")
async def quiz_progress(user_id: int = Depends(get_current_user_id)):
    """返回当前账号真实题库进度，不使用静态示例掌握度。"""
    db = get_connection()
    rows = db.execute("SELECT topic, score, total, created_at FROM quiz_attempts WHERE learner_id=? ORDER BY created_at", (str(user_id),)).fetchall()
    by_topic = {}
    for row in rows:
        topic = row[0] or '综合练习'; total = max(int(row[2] or 1), 1); score = int(row[1] or 0)
        item = by_topic.setdefault(topic, {'attempts': 0, 'correct': 0, 'total': 0})
        item['attempts'] += 1; item['correct'] += score; item['total'] += total
        if '|' in topic:
            category, _ = topic.split('|', 1)
            summary = by_topic.setdefault(category, {'attempts': 0, 'correct': 0, 'total': 0})
            summary['attempts'] += 1; summary['correct'] += score; summary['total'] += total
    return {'user_id': user_id, 'attempts': len(rows), 'topics': by_topic}


@router.post("/submit")
async def submit_quiz(req: QuizSubmitRequest, user_id: int = Depends(get_current_user_id)):
    """提交答题记录，自动触发画像更新（发布 QUIZ_SUBMITTED 事件）。"""
    db = get_connection()
    db.execute(
        "INSERT INTO quiz_attempts (learner_id, topic, score, total, payload) VALUES (?,?,?,?,?)",
        (str(user_id), req.topic, req.score, req.total, json.dumps({"source": "quiz_page"}))
    )
    db.commit()

    # P3: 发布答题事件，触发 AssessmentAgent 更新领域技能画像。
    # correct 用正确率 >= 0.6 作为信号（批量提交，非单题对错）。
    total = max(req.total, 1)
    correct = (req.score / total) >= 0.6
    await event_bus.publish(
        "QUIZ_SUBMITTED",
        {
            "topic": req.topic,
            "correct": correct,
            "difficulty": "medium",
            "user_id": user_id,
            "score": req.score,
            "total": req.total,
        },
        source="quiz_router",
    )
    return {"success": True, "message": f"答题记录已保存: {req.score}/{req.total}", "user_id": user_id}
