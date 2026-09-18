from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from ..models.journey import get_journey, save_journey, JourneyStep
from ..core.event_bus import event_bus
from ..core.websocket_manager import websocket_manager

router = APIRouter(prefix="/api/journey", tags=["journey"])

class JourneyStepResponse(BaseModel):
    id: int
    label: str
    icon: str
    href: str
    completed: bool
    active: bool
    completed_at: Optional[str]

class JourneyResponse(BaseModel):
    steps: List[JourneyStepResponse]
    current_step_id: int
    overall_progress: float
    updated_at: str

class StepCompleteRequest(BaseModel):
    step_id: int
      # DEMO-ONLY: user_id from JWT in production
user_id: int = 1

@router.get("", response_model=JourneyResponse)
async def get_journey_data(  # DEMO-ONLY: user_id from JWT in production
user_id: int = 1):
    """获取学习旅程数据"""
    journey = get_journey(user_id)
    return {
        "steps": [
            {
                "id": s.id,
                "label": s.label,
                "icon": s.icon,
                "href": s.href,
                "completed": s.completed,
                "active": s.active,
                "completed_at": s.completed_at
            }
            for s in journey.steps
        ],
        "current_step_id": journey.current_step_id,
        "overall_progress": journey.overall_progress,
        "updated_at": journey.updated_at
    }

@router.post("/complete-step")
async def complete_step(request: StepCompleteRequest):
    """完成某个步骤"""
    journey = get_journey(request.user_id)
    journey.complete_step(request.step_id)
    save_journey(journey)

    # 触发事件
    await event_bus.publish(
        "STEP_COMPLETED",
        {
            "step_id": request.step_id,
            "user_id": request.user_id
        },
        source="user"
    )

    # 推送到所有 WebSocket 连接
    await websocket_manager.broadcast({
        "type": "journey_update",
        "data": {
            "current_step": journey.current_step_id,
            "progress": journey.overall_progress
        }
    })

    return {"message": "步骤已完成", "journey": journey}

@router.get("/next-step")
async def get_next_step(  # DEMO-ONLY: user_id from JWT in production
user_id: int = 1):
    """获取下一步建议"""
    journey = get_journey(user_id)
    next_step = journey.get_next_step()
    if not next_step:
        return {"message": "[Party] 所有步骤已完成！", "done": True}
    return {
        "step": {
            "id": next_step.id,
            "label": next_step.label,
            "href": next_step.href,
            "icon": next_step.icon
        },
        "progress": journey.overall_progress,
        "done": False
    }