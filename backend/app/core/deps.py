"""FastAPI 依赖注入：JWT 认证与权限校验。"""
from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError

from .security import SECRET_KEY, ALGORITHM
from .database import get_connection


async def get_current_user(request: Request) -> dict:
    """从 Authorization 头提取 Bearer token，解码并校验用户。

    Returns:
        dict: {"id": int, "username": str, "role": str}

    Raises:
        401: 未提供令牌、令牌无效或用户不存在。
        403: 用户账号已被禁用。
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
        )

    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, role, is_active FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用",
        )

    return {"id": row["id"], "username": row["username"], "role": row["role"]}


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """要求管理员角色 —— 在 get_current_user 基础上增加角色检查。"""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


async def get_current_user_id(
    request: Request,
) -> int:
    """
    从 JWT 提取当前用户 ID，用于正式接口（画像、学习记录、成绩等）。
    无有效 token 时返回 401，不提供默认值。
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="无效的认证令牌")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM users WHERE username = ? AND is_active = 1", (username,)).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    return row["id"]
