# backend/app/routers/user_profile.py
import json
from fastapi import APIRouter, HTTPException, status
from app.core.database import get_connection
from app.schemas import UserProfileCreate, UserProfileUpdate, UserProfileResponse

router = APIRouter(prefix="/api/user-profile", tags=["user_profile"])


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: int):
    """获取用户画像（如果不存在则返回默认空画像）"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, interested_topics, strong_topics, weak_topics,
                   improvement_goals, has_completed_guide, created_at, updated_at
            FROM user_profiles WHERE user_id = ?
            """,
            (user_id,)
        )
        row = cursor.fetchone()

    if row is None:
        # 返回默认空画像
        return UserProfileResponse(
            id=0,
            user_id=user_id,
            interested_topics=[],
            strong_topics=[],
            weak_topics=[],
            improvement_goals=[],
            has_completed_guide=False,
            created_at=None,
            updated_at=None
        )

    return UserProfileResponse(
        id=row[0],
        user_id=row[1],
        interested_topics=json.loads(row[2]),
        strong_topics=json.loads(row[3]),
        weak_topics=json.loads(row[4]),
        improvement_goals=json.loads(row[5]),
        has_completed_guide=bool(row[6]),
        created_at=row[7],
        updated_at=row[8]
    )


@router.post("/{user_id}", response_model=UserProfileResponse)
def create_or_update_user_profile(user_id: int, profile_data: UserProfileUpdate):
    """创建或更新用户画像"""
    # 先检查用户是否存在
    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

    # 获取当前画像（判断是创建还是更新）
    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()

    # 准备 JSON 字段
    interested_topics = json.dumps(profile_data.interested_topics or [], ensure_ascii=False)
    strong_topics = json.dumps(profile_data.strong_topics or [], ensure_ascii=False)
    weak_topics = json.dumps(profile_data.weak_topics or [], ensure_ascii=False)
    improvement_goals = json.dumps(profile_data.improvement_goals or [], ensure_ascii=False)
    has_completed_guide = 1 if profile_data.has_completed_guide else 0

    with get_connection() as conn:
        if existing is None:
            # 创建新画像
            cursor = conn.execute(
                """
                INSERT INTO user_profiles
                (user_id, interested_topics, strong_topics, weak_topics, improvement_goals, has_completed_guide)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, interested_topics, strong_topics, weak_topics, improvement_goals, has_completed_guide)
            )
            conn.commit()
            profile_id = cursor.lastrowid
        else:
            # 更新现有画像
            conn.execute(
                """
                UPDATE user_profiles SET
                    interested_topics = ?,
                    strong_topics = ?,
                    weak_topics = ?,
                    improvement_goals = ?,
                    has_completed_guide = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (interested_topics, strong_topics, weak_topics, improvement_goals, has_completed_guide, user_id)
            )
            conn.commit()
            profile_id = existing[0]

    # 返回更新后的数据
    return get_user_profile(user_id)


@router.patch("/{user_id}/complete-guide")
def complete_guide(user_id: int):
    """标记用户已完成引导流程"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM user_profiles WHERE user_id = ?", (user_id,))
        if cursor.fetchone() is None:
            # 如果没有画像，先创建空画像并标记已完成
            conn.execute(
                """
                INSERT INTO user_profiles (user_id, has_completed_guide)
                VALUES (?, 1)
                """,
                (user_id,)
            )
        else:
            conn.execute(
                "UPDATE user_profiles SET has_completed_guide = 1, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
        conn.commit()

    return {"message": "引导流程已完成", "user_id": user_id}