# backend/app/routers/auth.py
from fastapi import APIRouter, HTTPException, status
from app.core.database import get_connection
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas import UserCreate, UserLogin, Token, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(user_data: UserCreate):
    with get_connection() as conn:
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该用户已存在，请换一个用户名"
            )

        hashed_pw = get_password_hash(user_data.password)
        role = user_data.role if user_data.role in ("user", "admin") else "user"
        cursor = conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (user_data.username, hashed_pw, role)
        )
        user_id = cursor.lastrowid
        conn.commit()

        cursor = conn.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

    # 新注册用户一定是新用户，没有画像也没有完成引导
    token = create_access_token(data={"sub": user_data.username})
    return Token(
        access_token=token,
        user=UserOut(id=row[0], username=row[1], role=row[2]),
        is_new_user=True,
        has_completed_guide=False,
    )


@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    with get_connection() as conn:
        # [OK] 查询时加上 is_active 字段
        cursor = conn.execute(
            "SELECT id, username, hashed_password, role, is_active FROM users WHERE username = ?",
            (user_data.username,)
        )
        row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 用字典方式取值
    user_dict = dict(row)
    user_id = user_dict["id"]
    username = user_dict["username"]
    hashed_pw = user_dict["hashed_password"]
    role = user_dict["role"]
    is_active = user_dict.get("is_active", 1)  # 默认为启用

    # [OK] 检查用户是否被禁用
    if is_active == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账号已被禁用，请联系管理员"
        )

    if not verify_password(user_data.password, hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # [OK] 更新最后登录时间
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()

    # [NEW] 检查是否为新用户（未完成画像评估 + 未完成引导）
    is_new_user = False
    has_completed_guide = False
    with get_connection() as conn:
        # 检查 learner_profiles 是否存在且有评分
        lp = conn.execute(
            "SELECT dialogue_completed, theoretical_basis, coding_ability, practical_ops, "
            "troubleshooting, data_thinking, self_learning "
            "FROM learner_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        has_profile = lp is not None
        has_scores = False
        if has_profile:
            scores = [lp["theoretical_basis"], lp["coding_ability"], lp["practical_ops"],
                      lp["troubleshooting"], lp["data_thinking"], lp["self_learning"]]
            has_scores = any(s and s > 0 for s in scores)

        # 检查 user_profiles 引导完成状态
        up = conn.execute(
            "SELECT has_completed_guide FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        has_completed_guide = bool(up["has_completed_guide"]) if up else False

        # 新用户 = 没有画像评分 且 没有完成引导
        is_new_user = not has_scores and not has_completed_guide

    token = create_access_token(data={"sub": username})
    return Token(
        access_token=token,
        user=UserOut(id=user_id, username=username, role=role),
        is_new_user=is_new_user,
        has_completed_guide=has_completed_guide,
    )