from fastapi import Depends
from ..core.deps import get_current_user_id
from fastapi import APIRouter, Query
from datetime import date as date_type
from typing import List
from pydantic import BaseModel

from ..core.database import get_connection

router = APIRouter(prefix="/learning-records", tags=["learning_records"])

class RecordCreate(BaseModel):
    date: date_type
    study_minutes: int = 0
    completed_lectures: int = 0
    accuracy: float = 0.0
    is_logged_in: bool = True

class RecordResponse(BaseModel):
    date: str
    study_minutes: int
    completed_lectures: int
    accuracy: float
    is_logged_in: bool


@router.get("/", response_model=List[RecordResponse])
def get_month_records(
    year: int = Query(...),
    month: int = Query(...),
    user_id: int = Depends(get_current_user_id),
):
    """获取指定月份的学习记录"""
    start_date = f"{year}-{month:02d}-01"
    # 计算下个月第一天
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT date, study_minutes, completed_lectures, accuracy, is_logged_in
            FROM learning_records
            WHERE user_id = ? AND date >= ? AND date < ?
            ORDER BY date
            """,
            (user_id, start_date, end_date)
        ).fetchall()

    return [
        {
            "date": row[0],
            "study_minutes": row[1],
            "completed_lectures": row[2],
            "accuracy": row[3],
            "is_logged_in": bool(row[4]),
        }
        for row in rows
    ]


@router.post("/", status_code=201)
def create_or_update_record(record: RecordCreate, user_id: int = Depends(get_current_user_id)):
    """创建或更新某天的学习记录"""
    date_str = record.date.isoformat()
    with get_connection() as conn:
        # 检查是否已有记录
        existing = conn.execute(
            "SELECT id FROM learning_records WHERE user_id = ? AND date = ?",
            (user_id, date_str)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE learning_records
                SET study_minutes = study_minutes + ?,
                    completed_lectures = completed_lectures + ?,
                    accuracy = CASE WHEN ? > 0 THEN ? ELSE accuracy END,
                    is_logged_in = ?
                WHERE user_id = ? AND date = ?
                """,
                (
                    record.study_minutes,
                    record.completed_lectures,
                    record.accuracy,
                    record.accuracy,
                    1 if record.is_logged_in else 0,
                    user_id,
                    date_str
                )
            )
        else:
            conn.execute(
                """
                INSERT INTO learning_records
                (user_id, date, study_minutes, completed_lectures, accuracy, is_logged_in)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    date_str,
                    record.study_minutes,
                    record.completed_lectures,
                    record.accuracy,
                    1 if record.is_logged_in else 0,
                )
            )
        conn.commit()

    return {"message": "saved"}
