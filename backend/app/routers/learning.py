"""学习闭环路由 — 按需触发下一轮资源生成。"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/learning", tags=["learning"])


class NextRoundRequest(BaseModel):
    user_id: int = 1
    topic: Optional[str] = None
    mode: str = "study"


@router.post("/next-round")
async def next_round(req: NextRoundRequest):
    """按需生成下一轮学习资源(与 /api/lecture/{id}/{num}/multi-agent 同结构)。

    - 提供 topic 时按该主题反查讲次;否则用领域技能画像最低分技能定位。
    - 复用 VerificationOrchestrator 完整审核闭环。
    """
    from ..agents.next_round import get_next_round_coordinator
    coordinator = get_next_round_coordinator()
    return await coordinator.generate_next_round(req.user_id, req.topic, req.mode)
