from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import date as date_type
from typing import List
from pydantic import BaseModel

from ..core.database import get_connection
from ..core.deps import get_current_user_id, get_current_admin

router = APIRouter(prefix="/daily-tasks", tags=["daily_tasks"])

class TaskCreate(BaseModel):
    date: date_type
    content: str
    category: str = "custom"

class TaskResponse(BaseModel):
    id: int
    date: str
    content: str
    category: str
    is_done: bool

class TaskUpdate(BaseModel):
    is_done: bool


@router.get("/", response_model=List[TaskResponse])
def get_tasks(date: date_type = Query(...), user_id: int = Depends(get_current_user_id)):
    """获取指定日期的任务列表"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, date, content, category, is_done FROM daily_tasks WHERE user_id = ? AND date = ? ORDER BY id",
            (user_id, date.isoformat())
        ).fetchall()
    return [
        {
            "id": row[0],
            "date": row[1],
            "content": row[2],
            "category": row[3],
            "is_done": bool(row[4]),
        }
        for row in rows
    ]


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, user_id: int = Depends(get_current_user_id)):
    """添加新任务"""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO daily_tasks (user_id, date, content, category, is_done) VALUES (?, ?, ?, ?, ?)",
            (user_id, task.date.isoformat(), task.content, task.category, 0)
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, date, content, category, is_done FROM daily_tasks WHERE id = ?",
            (new_id,)
        ).fetchone()
    return {
        "id": row[0],
        "date": row[1],
        "content": row[2],
        "category": row[3],
        "is_done": bool(row[4]),
    }


@router.patch("/{task_id}")
def toggle_task(task_id: int, update: TaskUpdate, user_id: int = Depends(get_current_user_id)):
    """切换任务完成状态"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM daily_tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        conn.execute(
            "UPDATE daily_tasks SET is_done = ? WHERE id = ?",
            (1 if update.is_done else 0, task_id)
        )
        conn.commit()
    return {"message": "updated", "is_done": update.is_done}


@router.delete("/{task_id}")
def delete_task(task_id: int, user_id: int = Depends(get_current_user_id)):
    """删除任务"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM daily_tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        conn.execute("DELETE FROM daily_tasks WHERE id = ?", (task_id,))
        conn.commit()
    return {"message": "deleted"}


class TeacherTaskCreate(BaseModel):
    date: date_type
    content: str
    target_user_id: int


@router.post("/teacher", response_model=TaskResponse, status_code=201)
def create_teacher_task(task: TeacherTaskCreate, admin: dict = Depends(get_current_admin)):
    """教师向指定学生下发命令，学生端以 teacher 分类显示。"""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO daily_tasks (user_id, date, content, category, is_done) VALUES (?, ?, ?, 'teacher', 0)",
            (task.target_user_id, task.date.isoformat(), task.content),
        )
        conn.commit()
        row = conn.execute("SELECT id, date, content, category, is_done FROM daily_tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return {"id": row[0], "date": row[1], "content": row[2], "category": row[3], "is_done": bool(row[4])}
