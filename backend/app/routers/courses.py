"""课程路由 — 提供课程列表和课程详情。

前端学习空间（/learn 和 /learn/{id}）依赖这两个端点，
之前缺失导致课程列表页和详情页 404。
"""
from fastapi import APIRouter, HTTPException
from .lecture import list_courses, get_course_metadata

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("")
def get_courses():
    """列出所有课程（摘要信息）。"""
    courses = list_courses()
    return {"success": True, "courses": courses}


@router.get("/{course_id}")
def get_course(course_id: str):
    """获取单个课程详情（含模块和讲次）。"""
    course = get_course_metadata(course_id)
    if not course:
        raise HTTPException(status_code=404, detail=f"课程不存在: {course_id}")
    return {"success": True, "course": course}
