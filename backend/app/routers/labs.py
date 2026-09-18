"""Experiment and dataset routes."""
import json
import logging
from fastapi import APIRouter, HTTPException, Query, Depends

from ..core.database import get_connection, get_lab, list_datasets, list_knowledge_points, list_labs
from ..core.deps import get_current_user
from ..agents.lab_generator_agent import LabGeneratorAgent
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/labs", tags=["labs"])


class GenerateLabRequest(BaseModel):
    topic: str
    key_concepts: list[str]
    difficulty: str = "medium"


class LabCompleteRequest(BaseModel):
    lab_id: str

    @field_validator("lab_id")
    @classmethod
    def validate_lab_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise HTTPException(status_code=400, detail="lab_id 不能为空")
        if len(v) > 100:
            raise HTTPException(status_code=400, detail="lab_id 长度超限")
        return v.strip()


@router.post("/generate")
async def generate_lab(request: GenerateLabRequest):
    """根据讲次主题和关键概念自动生成实验题目"""
    try:
        agent = LabGeneratorAgent()
        lab_data = agent.generate_lab(request.topic, request.key_concepts, request.difficulty)
        return {"success": True, "data": lab_data}
    except Exception as e:
        logger.error(f"Lab generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"生成实验题目失败: {str(e)}")


@router.get("")
async def get_labs(
    topic: str | None = Query(None, description="Filter by topic"),
    category: str | None = Query(None, description="Filter by category"),
):
    labs = list_labs(topic=topic, category=category)
    return {"total": len(labs), "labs": labs}


@router.get("/datasets")
async def get_datasets():
    datasets = list_datasets()
    return {"total": len(datasets), "datasets": datasets}


@router.get("/knowledge-points")
async def get_knowledge_points():
    points = list_knowledge_points()
    return {"total": len(points), "knowledge_points": points}


@router.get("/{lab_id}")
async def get_lab_detail(lab_id: str):
    lab = get_lab(lab_id)
    if not lab:
        raise HTTPException(404, f"实验 {lab_id} 不存在")
    return lab


@router.post("/complete")
def complete_lab(req: LabCompleteRequest, current_user: dict = Depends(get_current_user)):
    """完成实验，记录学习事件并触发画像更新"""
    user_id = current_user["id"]
    try:
        db = get_connection()
        db.execute(
            "INSERT INTO learning_events (learner_id, event_type, payload) VALUES (?,?,?)",
            (user_id, "lab_completed", json.dumps({"lab_id": req.lab_id}))
        )
        db.commit()
        return {"success": True, "message": f"实验 {req.lab_id} 完成", "user_id": user_id}
    except Exception as e:
        logger.error(f"Lab complete failed: {e}")
        raise HTTPException(status_code=500, detail=f"记录实验完成失败: {str(e)}")
