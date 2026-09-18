from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ..agents.lab_grader import get_lab_grader
from ..core.event_bus import event_bus

router = APIRouter(prefix="/api/lab-grader", tags=["lab-grader"])

class GradeRequest(BaseModel):
    code: str
    lab_title: str
    task_description: Optional[str] = ""
    user_id: int = 1

class GradeResponse(BaseModel):
    score: int
    passed: bool
    errors: List[str]
    suggestions: List[str]
    comment: str

@router.post("/grade", response_model=GradeResponse)
async def grade_code(request: GradeRequest):
    """批改实验代码"""
    try:
        grader = get_lab_grader()
        result = await grader.grade_code(   # ← 这里添加 await
            code=request.code,
            lab_title=request.lab_title,
            task_description=request.task_description
        )
        # P3: 发布实训完成事件，触发 AssessmentAgent 更新领域技能画像。
        await event_bus.publish(
            "LAB_COMPLETED",
            {
                "lab_name": request.lab_title,
                "topic": request.lab_title,
                "score": result.get("score"),
                "user_id": request.user_id,
            },
            source="lab_grader_router",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批改失败: {str(e)}")