# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_connection
from app.schemas import UserOut
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ===== 扩展的用户输出模型（包含新字段） =====
class AdminUserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


# ===== 获取所有用户列表 =====
@router.get("/users", response_model=List[AdminUserOut])
def get_all_users():
    """获取所有用户列表（仅管理员）"""
    with get_connection() as conn:
        # [OK] 查询所有字段（包括新增的 is_active, created_at, last_login_at）
        cursor = conn.execute(
            "SELECT id, username, role, is_active, created_at, last_login_at FROM users ORDER BY id"
        )
        rows = cursor.fetchall()
        return [
            AdminUserOut(
                id=row[0],
                username=row[1],
                role=row[2],
                is_active=bool(row[3]),  # 转为布尔值
                created_at=row[4],
                last_login_at=row[5]
            )
            for row in rows
        ]


# ===== 修改用户角色 =====
@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def update_user_role(user_id: int, role: str):
    """修改用户角色（仅管理员）"""
    if role not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色必须是 'user' 或 'admin'"
        )

    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        conn.commit()

        # [OK] 返回更新后的用户信息（包含所有字段）
        cursor = conn.execute(
            "SELECT id, username, role, is_active, created_at, last_login_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return AdminUserOut(
            id=row[0],
            username=row[1],
            role=row[2],
            is_active=bool(row[3]),
            created_at=row[4],
            last_login_at=row[5]
        )


# ===== [NEW] 禁用/启用用户 =====
@router.patch("/users/{user_id}/toggle-active", response_model=AdminUserOut)
def toggle_user_active(user_id: int):
    """禁用/启用用户（仅管理员）"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT id, is_active FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 切换状态：1→0 或 0→1
        current_status = row[1]
        new_status = 0 if current_status == 1 else 1

        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (new_status, user_id)
        )
        conn.commit()

        # 返回更新后的用户信息
        cursor = conn.execute(
            "SELECT id, username, role, is_active, created_at, last_login_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return AdminUserOut(
            id=row[0],
            username=row[1],
            role=row[2],
            is_active=bool(row[3]),
            created_at=row[4],
            last_login_at=row[5]
        )