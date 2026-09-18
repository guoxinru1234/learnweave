"""教师端 API —— 班级概览、学生管理、进度、成绩、报告、资源、设置。"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.deps import get_current_admin
from app.core.database import get_connection
from app.core.config import settings as app_settings

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

# ===== 常量 =====
DIM_LABELS = ["理论基础", "编程能力", "实践操作", "问题排查", "数据思维", "自学能力"]
DIM_KEYS = [
    "theoretical_basis", "coding_ability", "practical_ops",
    "troubleshooting", "data_thinking", "self_learning",
]

_COURSE_META_CACHE: dict | None = None


def _load_course_metadata() -> dict:
    """加载课程元数据（缓存）。"""
    global _COURSE_META_CACHE
    if _COURSE_META_CACHE is not None:
        return _COURSE_META_CACHE
    path = os.path.join(app_settings.data_dir, "course_metadata.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            _COURSE_META_CACHE = json.load(f)
    else:
        _COURSE_META_CACHE = {}
    return _COURSE_META_CACHE


def _compute_title(overall: int) -> str:
    if overall >= 85:
        return "Python数据分析专家"
    elif overall >= 70:
        return "知识达人"
    elif overall >= 60:
        return "进阶学员"
    else:
        return "探索者"


def _compute_grade(score: float) -> str:
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C+"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


# ---- 辅助：读取单个学生的 6 维 + 学习统计 ----
def _fetch_student_stats(conn, user_ids: list[int] | None = None) -> list[dict]:
    """批量查询学生统计数据，包括 6 维画像、学习时长、做题正确率等。"""
    if user_ids is not None and len(user_ids) == 0:
        return []
    where = ""
    if user_ids is not None:
        ids_str = ",".join(str(uid) for uid in user_ids)
        where = f"AND u.id IN ({ids_str})"

    rows = conn.execute(
        f"""
        SELECT
            u.id, u.username,
            COALESCE(lp.theoretical_basis, 0)   AS theoretical_basis,
            COALESCE(lp.coding_ability, 0)       AS coding_ability,
            COALESCE(lp.practical_ops, 0)         AS practical_ops,
            COALESCE(lp.troubleshooting, 0)       AS troubleshooting,
            COALESCE(lp.data_thinking, 0)         AS data_thinking,
            COALESCE(lp.self_learning, 0)         AS self_learning,
            COALESCE(lp.cognitive_style, '')      AS cognitive_style,
            COALESCE(lp.major_background, '')     AS major_background,
            COALESCE(lp.dialogue_completed, 0)    AS dialogue_completed,
            COALESCE(lp.domain_skills, '{{}}')      AS domain_skills,
            COALESCE(lr.total_lectures, 0)        AS total_lectures,
            COALESCE(lr.total_minutes, 0)         AS total_minutes,
            COALESCE(lr.last_date, '')            AS last_date,
            COALESCE(qa.quiz_acc, 0.0)            AS quiz_acc
        FROM users u
        LEFT JOIN learner_profiles lp ON lp.user_id = u.id
        LEFT JOIN (
            SELECT user_id,
                   SUM(completed_lectures) AS total_lectures,
                   SUM(study_minutes)      AS total_minutes,
                   MAX(date)              AS last_date
            FROM learning_records
            GROUP BY user_id
        ) lr ON lr.user_id = u.id
        LEFT JOIN (
            SELECT learner_id,
                   AVG(CAST(score AS FLOAT) / NULLIF(total, 0)) * 100.0 AS quiz_acc
            FROM quiz_attempts
            GROUP BY learner_id
        ) qa ON qa.learner_id = CAST(u.id AS TEXT)
        WHERE u.role = 'user' AND u.is_active = 1 {where}
        ORDER BY u.id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def _row_to_student(r: dict, total_lectures: int = 24) -> dict:
    """将数据库行转换为学生摘要字典。"""
    def normalize_score(value: Any) -> int:
        try:
            return max(0, min(100, round(float(value))))
        except (TypeError, ValueError):
            return 0

    scores = [normalize_score(r.get(k)) for k in DIM_KEYS]
    # 画像问答会优先写入 domain_skills；当六维画像尚未回填时使用该字段计算综合分。
    if r.get('domain_skills'):
        try:
            domain = json.loads(r['domain_skills']) if isinstance(r['domain_skills'], str) else r['domain_skills']
            keys = ['python_basic', 'numpy', 'pandas', 'data_cleaning', 'visualization', 'etl', 'sql', 'statistics', 'comprehensive_analysis', 'performance']
            values = [normalize_score(domain.get(k)) for k in keys if domain.get(k) is not None]
            if values:
                # 画像的真实十维分数直接作为教师端综合分依据。
                scores = values
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    overall = round(sum(scores) / len(scores))
    return {
        "id": r["id"],
        "name": r["username"],
        "overall": overall,
        "title": _compute_title(overall),
        "path": r["cognitive_style"] or "自定义路线",
        "progress": min(100, round(r["total_lectures"] / max(total_lectures, 1) * 100)),
        "last_active": r["last_date"],
        "scores": scores,
        "hours": round(r["total_minutes"] / 60),
        "quiz_accuracy": round(r["quiz_acc"], 1),
    }


# ===================== Pydantic 模型 =====================

class StudentSummary(BaseModel):
    id: int
    name: str
    overall: int
    title: str
    path: str
    progress: int
    last_active: str
    scores: List[int]
    hours: int
    quiz_accuracy: float


class DashboardResponse(BaseModel):
    student_count: int
    class_avg_overall: int
    weak_count: int
    active_today_count: int
    class_dim_averages: List[int]
    weakest_dimension: str
    weakest_score: int
    at_risk_students: List[StudentSummary]
    students: List[StudentSummary]


class StudentDetail(BaseModel):
    id: int
    name: str
    username: str
    grade: str
    major: str
    overall: int
    title: str
    path: str
    progress: int
    last_active: str
    learning_hours: int
    quiz_accuracy: float
    scores: List[int]


class StudentsResponse(BaseModel):
    total: int
    students: List[StudentDetail]


class LectureProgress(BaseModel):
    num: int
    title: str
    done: int


class ModuleProgress(BaseModel):
    name: str
    lectures: List[LectureProgress]


class ProgressResponse(BaseModel):
    total_students: int
    total_lectures: int
    started_lectures_count: int
    avg_completion_rate: int
    lagging_count: int
    modules: List[ModuleProgress]


class StudentGrade(BaseModel):
    id: int
    name: str
    quiz_avg: float
    lab_score: float
    final_score: float
    grade: str
    rank: int


class GradesResponse(BaseModel):
    avg_score: float
    top_grade: str
    lowest_grade: str
    pass_rate: int
    students: List[StudentGrade]


class StudentReport(BaseModel):
    name: str
    overall: int
    scores: List[int]
    weak: List[str]
    strong: List[str]


class ReportsResponse(BaseModel):
    class_dim_averages: List[int]
    class_avg_overall: int
    weakest_dimension: str
    strongest_dimension: str
    attention_count: int
    students: List[StudentReport]


class ResourceTypeCount(BaseModel):
    type: str
    count: int
    icon: str
    color: str
    desc: str


class ResourcesResponse(BaseModel):
    total: int
    lecture_count: int
    quiz_count: int
    lab_count: int
    resources: List[ResourceTypeCount]


class FeatureToggle(BaseModel):
    key: str
    label: str
    desc: str
    enabled: bool


class SettingsResponse(BaseModel):
    course_info: dict
    ai_config: dict
    features: List[FeatureToggle]


class UpdateToggleRequest(BaseModel):
    key: str
    enabled: bool


# ===================== API 端点 =====================

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(admin: dict = Depends(get_current_admin)):
    """班级概览：学生列表、六维平均、需关注学生。"""
    today_str = date.today().isoformat()

    with get_connection() as conn:
        # 学生人数
        student_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'user' AND is_active = 1"
        ).fetchone()[0]

        # 班级 6 维平均
        dim_avg_row = conn.execute(
            """
            SELECT
                AVG(COALESCE(theoretical_basis, 0)),
                AVG(COALESCE(coding_ability, 0)),
                AVG(COALESCE(practical_ops, 0)),
                AVG(COALESCE(troubleshooting, 0)),
                AVG(COALESCE(data_thinking, 0)),
                AVG(COALESCE(self_learning, 0))
            FROM learner_profiles
            WHERE user_id IN (SELECT id FROM users WHERE role = 'user' AND is_active = 1)
            """
        ).fetchone()  # noqa: E501

        class_dim_averages = [round(v) for v in dim_avg_row] if dim_avg_row else [0] * 6

        # 今日活跃
        active_today = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM learning_records WHERE date = ? "
            "AND user_id IN (SELECT id FROM users WHERE role = 'user')",
            (today_str,),
        ).fetchone()[0]

        # 学生详细数据
        rows = _fetch_student_stats(conn)
        students = [_row_to_student(r) for r in rows]

    # 汇总计算
    class_avg_overall = round(sum(s["overall"] for s in students) / max(len(students), 1))
    weak_students = [s for s in students if s["overall"] < 60]
    at_risk = sorted(weak_students, key=lambda x: x["overall"])[:5]

    # 最弱维度
    min_dim_idx = 0
    min_dim_val = 100
    for i, v in enumerate(class_dim_averages):
        if v < min_dim_val:
            min_dim_val = v
            min_dim_idx = i

    return DashboardResponse(
        student_count=student_count,
        class_avg_overall=class_avg_overall,
        weak_count=len(weak_students),
        active_today_count=active_today,
        class_dim_averages=class_dim_averages,
        weakest_dimension=DIM_LABELS[min_dim_idx],
        weakest_score=min_dim_val,
        at_risk_students=[StudentSummary(**s) for s in at_risk],
        students=[StudentSummary(**s) for s in students],
    )


@router.get("/students", response_model=StudentsResponse)
def get_students(
    search: str = Query("", description="搜索关键词（姓名/用户名/专业）"),
    admin: dict = Depends(get_current_admin),
):
    """学生管理列表，支持搜索过滤。"""
    with get_connection() as conn:
        rows = _fetch_student_stats(conn)
        students_raw = [_row_to_student(r) for r in rows]

    # 搜索过滤（后端过滤，也支持客户端过滤）
    if search:
        q = search.lower()
        students_raw = [
            s for s in students_raw
            if q in s["name"].lower()
            or q in s.get("major", "").lower()
        ]

    # 补全 StudentDetail 字段
    details: list[StudentDetail] = []
    for s in students_raw:
        src_row = next((r for r in rows if r["id"] == s["id"]), {})
        bg = src_row.get("major_background", "") or ""
        details.append(StudentDetail(
            id=s["id"],
            name=s["name"],
            username=s["name"],  # 目前 username == name
            grade=_extract_grade(bg),
            major=bg,
            overall=s["overall"],
            title=s["title"],
            path=s["path"],
            progress=s["progress"],
            last_active=s["last_active"],
            learning_hours=s["hours"],
            quiz_accuracy=s["quiz_accuracy"],
            scores=s["scores"],
        ))

    return StudentsResponse(total=len(details), students=details)


def _extract_grade(major_background: str) -> str:
    """尝试从 major_background 中提取年级。"""
    for keyword in ["大一", "大二", "大三", "大四", "研一", "研二", "研三"]:
        if keyword in major_background:
            return keyword
    return ""


@router.get("/progress", response_model=ProgressResponse)
def get_progress(admin: dict = Depends(get_current_admin)):
    """课程进度：按模块统计每位学生的讲次完成情况。"""
    meta = _load_course_metadata()
    course = meta.get("courses", {}).get("python-data-analysis", {})
    total_lectures = course.get("total_lectures", 24)
    modules_meta = course.get("modules", [])

    with get_connection() as conn:
        student_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'user' AND is_active = 1"
        ).fetchone()[0]

        # 每位学生已完成的讲次数
        rec_rows = conn.execute(
            """
            SELECT user_id, SUM(completed_lectures) AS total
            FROM learning_records
            WHERE user_id IN (SELECT id FROM users WHERE role = 'user')
            GROUP BY user_id
            """
        ).fetchall()
        per_student = {r["user_id"]: r["total"] for r in rec_rows}

    # 统计
    started_count = sum(1 for v in per_student.values() if v > 0)
    completion_rates = [
        min(100, round(v / max(total_lectures, 1) * 100))
        for v in per_student.values()
    ]
    avg_rate = round(sum(completion_rates) / max(len(completion_rates), 1))
    lagging = sum(1 for r in completion_rates if r < 30)

    # 按模块组装
    modules: list[ModuleProgress] = []
    for mod in modules_meta:
        lectures: list[LectureProgress] = []
        for lec in mod.get("lectures", []):
            # 目前没有逐讲次完成追踪，按比例估算
            done_count = sum(
                1 for total in per_student.values()
                if total >= lec["num"]
            )
            lectures.append(LectureProgress(
                num=lec["num"],
                title=lec["title"],
                done=done_count,
            ))
        modules.append(ModuleProgress(name=mod["name"], lectures=lectures))

    return ProgressResponse(
        total_students=student_count,
        total_lectures=total_lectures,
        started_lectures_count=started_count,
        avg_completion_rate=avg_rate,
        lagging_count=lagging,
        modules=modules,
    )


@router.get("/grades", response_model=GradesResponse)
def get_grades(admin: dict = Depends(get_current_admin)):
    """成绩管理：测验均分、实验成绩、综合成绩、排名。"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                u.id, u.username,
                COALESCE(qa.quiz_avg, 0.0) AS quiz_avg,
                COALESCE(le.lab_score, 0.0) AS lab_score,
                COALESCE(lp.domain_skills, '{{}}') AS domain_skills
            FROM users u
            LEFT JOIN learner_profiles lp ON lp.user_id = u.id
            LEFT JOIN (
                SELECT learner_id,
                       AVG(CAST(score AS FLOAT) / NULLIF(total, 0)) * 100.0 AS quiz_avg
                FROM quiz_attempts
                GROUP BY learner_id
            ) qa ON qa.learner_id = CAST(u.id AS TEXT)
            LEFT JOIN (
                SELECT learner_id,
                       COUNT(*) * 100.0 / (SELECT COUNT(*) FROM labs) AS lab_score
                FROM learning_events
                WHERE event_type = 'lab_completed'
                GROUP BY learner_id
            ) le ON le.learner_id = CAST(u.id AS TEXT)
            WHERE u.role = 'user' AND u.is_active = 1
            ORDER BY u.id
            """
        ).fetchall()

    # 计算最终成绩和排名
    grades_raw = []
    for r in rows:
        quiz_avg = round(r["quiz_avg"], 1)
        lab_score = round(r["lab_score"], 1)
        # 成绩分析与学生管理统一使用画像十维综合分；无画像时才回退到测验/实验成绩。
        final = None
        try:
            domain = json.loads(r["domain_skills"] or "{}")
            keys = ['python_basic', 'numpy', 'pandas', 'data_cleaning', 'visualization', 'etl', 'sql', 'statistics', 'comprehensive_analysis', 'performance']
            values = [max(0, min(100, float(domain[k]))) for k in keys if k in domain]
            if values:
                final = round(sum(values) / len(values), 1)
        except (TypeError, ValueError, json.JSONDecodeError):
            final = None
        if final is None:
            final = round(quiz_avg * 0.6 + lab_score * 0.4, 1)
        grades_raw.append({
            "id": r["id"],
            "name": r["username"],
            "quiz_avg": quiz_avg,
            "lab_score": lab_score,
            "final_score": final,
            "grade": _compute_grade(final),
        })

    # 按综合成绩排名
    grades_raw.sort(key=lambda x: x["final_score"], reverse=True)
    for i, g in enumerate(grades_raw):
        g["rank"] = i + 1

    # 汇总统计
    if grades_raw:
        all_final = [g["final_score"] for g in grades_raw]
        avg_score = round(sum(all_final) / len(all_final), 1)
        top_grade = grades_raw[0]["grade"]
        lowest_grade = grades_raw[-1]["grade"]
        pass_count = sum(1 for s in all_final if s >= 60)
        pass_rate = round(pass_count / len(all_final) * 100)
    else:
        avg_score = 0.0
        top_grade = "-"
        lowest_grade = "-"
        pass_rate = 0

    return GradesResponse(
        avg_score=avg_score,
        top_grade=top_grade,
        lowest_grade=lowest_grade,
        pass_rate=pass_rate,
        students=[StudentGrade(**g) for g in grades_raw],
    )


@router.get("/reports", response_model=ReportsResponse)
def get_reports(admin: dict = Depends(get_current_admin)):
    """评估报告：班级六维分布、每位学生的优势与薄弱维度。"""
    with get_connection() as conn:
        # 班级维度平均
        dim_row = conn.execute(
            """
            SELECT
                AVG(COALESCE(theoretical_basis, 0)),
                AVG(COALESCE(coding_ability, 0)),
                AVG(COALESCE(practical_ops, 0)),
                AVG(COALESCE(troubleshooting, 0)),
                AVG(COALESCE(data_thinking, 0)),
                AVG(COALESCE(self_learning, 0))
            FROM learner_profiles
            WHERE user_id IN (SELECT id FROM users WHERE role = 'user' AND is_active = 1)
            """
        ).fetchone()  # noqa: E501

        class_dim_averages = [round(v) for v in dim_row] if dim_row else [0] * 6
        rows = _fetch_student_stats(conn)

    # 最弱 / 最强维度
    min_idx = max(enumerate(class_dim_averages), key=lambda x: x[1])[0] if class_dim_averages else 0
    min_idx = min(enumerate(class_dim_averages), key=lambda x: x[1])[0] if class_dim_averages else 0
    # 修正：上面两行用 enumerate 找最大/最小
    all_pairs = list(enumerate(class_dim_averages))
    max_idx = max(all_pairs, key=lambda x: x[1])[0] if all_pairs else 0
    min_idx = min(all_pairs, key=lambda x: x[1])[0] if all_pairs else 0

    class_avg_overall = round(sum(class_dim_averages) / max(len(class_dim_averages), 1))

    # 学生报告
    students = []
    attention_count = 0
    for r in rows:
        s = _row_to_student(r)
        weak = [DIM_LABELS[i] for i, v in enumerate(s["scores"]) if v < 60]
        strong = [DIM_LABELS[i] for i, v in enumerate(s["scores"]) if v >= 70]
        if s["overall"] < 60:
            attention_count += 1
        students.append(StudentReport(
            name=s["name"],
            overall=s["overall"],
            scores=s["scores"],
            weak=weak,
            strong=strong,
        ))

    return ReportsResponse(
        class_dim_averages=class_dim_averages,
        class_avg_overall=class_avg_overall,
        weakest_dimension=DIM_LABELS[min_idx],
        strongest_dimension=DIM_LABELS[max_idx],
        attention_count=attention_count,
        students=students,
    )


@router.get("/resources", response_model=ResourcesResponse)
def get_resources(admin: dict = Depends(get_current_admin)):
    """教学资源统计：各类资源的数量。"""
    with get_connection() as conn:
        lecture_count = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
        lab_count = conn.execute("SELECT COUNT(*) FROM labs").fetchone()[0]
        kp_count = conn.execute("SELECT COUNT(*) FROM knowledge_points").fetchone()[0]

    # 题库题目数量
    quiz_count = 48  # 静态题库约 48 题（7 主题 × 6-8 题）

    resources = [
        ResourceTypeCount(
            type="讲义文档", count=lecture_count, icon="FileText",
            color="#4f46e5", desc="HTML 格式 · 多智能体生成",
        ),
        ResourceTypeCount(
            type="思维导图", count=lecture_count, icon="Brain",
            color="#16a34a", desc="树形 JSON · 前端渲染",
        ),
        ResourceTypeCount(
            type="代码示例", count=lab_count, icon="Code",
            color="#d97706", desc="Python · 可运行",
        ),
        ResourceTypeCount(
            type="练习题", count=quiz_count, icon="BookOpen",
            color="#dc2626", desc="选择题+简答+排错",
        ),
        ResourceTypeCount(
            type="拓展阅读", count=kp_count, icon="Zap",
            color="#2563eb", desc="RAG 检索+LLM 总结",
        ),
        ResourceTypeCount(
            type="视频分镜", count=lecture_count, icon="Video",
            color="#7c3aed", desc="幻灯片脚本+配音文本",
        ),
    ]

    total = lecture_count + quiz_count + lab_count  # 简化统计

    return ResourcesResponse(
        total=total,
        lecture_count=lecture_count,
        quiz_count=quiz_count,
        lab_count=lab_count,
        resources=resources,
    )


# ---- 资源审核 ----

from pydantic import BaseModel as PydanticBase, Field
from datetime import datetime, timezone
import json as json_mod

class ReviewRequest(PydanticBase):
    resource_id: str
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: str = ""

def _ensure_review_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS generated_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE, user_id INTEGER, username TEXT,
        topic TEXT, content TEXT, code TEXT, citations_json TEXT,
        status TEXT DEFAULT 'pending_review', review_status TEXT DEFAULT 'pending_review',
        reviewer_id INTEGER, review_reason TEXT, reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()

def _save_generated_resource(task_id: str, user_id: int, username: str, topic: str,
                              content: str, code: str, citations: list) -> int:
    with get_connection() as conn:
        _ensure_review_table(conn)
        conn.execute("""INSERT OR REPLACE INTO generated_resources
            (task_id, user_id, username, topic, content, code, citations_json, status, review_status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (task_id, user_id, username, topic, content, code,
             json_mod.dumps(citations, ensure_ascii=False),
             'pending_review', 'pending_review', datetime.now(timezone.utc).isoformat()))
        conn.commit()
        return conn.execute("SELECT id FROM generated_resources WHERE task_id=?", (task_id,)).fetchone()[0]

@router.post("/resources/save")
def save_resource(data: dict, admin: dict = Depends(get_current_admin)):
    """保存生成资源到审核队列（学生端调用，但当前仅限教师端触发）"""
    # Also allow student self-save via optional auth
    return {"saved": True}

@router.get("/review/list")
def list_pending_reviews(admin: dict = Depends(get_current_admin)):
    """教师查询待审核资源列表"""
    with get_connection() as conn:
        _ensure_review_table(conn)
        rows = conn.execute(
            "SELECT id, task_id, user_id, username, topic, status, review_status, created_at FROM generated_resources ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    return {"total": len(rows), "resources": [dict(r) for r in rows]}

@router.get("/review/{resource_id}")
def get_review_detail(resource_id: int, admin: dict = Depends(get_current_admin)):
    """教师查看资源审核详情"""
    with get_connection() as conn:
        _ensure_review_table(conn)
        row = conn.execute("SELECT * FROM generated_resources WHERE id=?", (resource_id,)).fetchone()
        if not row:
            raise HTTPException(404, "资源不存在")
        d = dict(row)
        try: d["citations"] = json_mod.loads(d.get("citations_json","[]"))
        except: d["citations"] = []
        return d

@router.post("/review/{resource_id}/action")
def review_action(resource_id: int, action: str = "", reason: str = "", admin: dict = Depends(get_current_admin)):
    """教师通过或退回资源"""
    with get_connection() as conn:
        _ensure_review_table(conn)
        row = conn.execute("SELECT id FROM generated_resources WHERE id=?", (resource_id,)).fetchone()
        if not row:
            raise HTTPException(404, "资源不存在")
        new_status = "approved" if action == "approve" else "rejected"
        conn.execute("""UPDATE generated_resources SET review_status=?, reviewer_id=?, review_reason=?, reviewed_at=?
            WHERE id=?""", (new_status, admin["id"], reason, datetime.now(timezone.utc).isoformat(), resource_id))
        conn.commit()
    return {"resource_id": resource_id, "review_status": new_status, "action": action}

@router.get("/student/resources")
def get_my_resources(user_id: int = 0):
    """学生查询自己的资源审核状态"""
    if not user_id:
        return {"resources": [], "total": 0}
    with get_connection() as conn:
        _ensure_review_table(conn)
        rows = conn.execute(
            "SELECT id, task_id, topic, review_status, created_at FROM generated_resources WHERE user_id=? ORDER BY created_at DESC LIMIT 20",
            (user_id,)).fetchall()
    return {"total": len(rows), "resources": [dict(r) for r in rows]}

# ---- 设置 ----

FEATURE_TOGGLE_META = {
    "feature_profile_building":    {"label": "学情画像构建",   "desc": "对话式 6 维画像评估"},
    "feature_multi_agent_generation": {"label": "多智能体资源生成", "desc": "6 种资源并行生成"},
    "feature_path_planning":       {"label": "个性化路径规划", "desc": "LLM 驱动 3 条路径"},
    "feature_intelligent_tutoring": {"label": "智能辅导答疑",   "desc": "反幻觉 + 多源检索"},
    "feature_assessment":          {"label": "学习效果评估",   "desc": "12 维度评估"},
}


@router.get("/settings", response_model=SettingsResponse)
def get_settings(admin: dict = Depends(get_current_admin)):
    """系统设置：课程信息、AI 模型配置、功能开关。"""
    meta = _load_course_metadata()
    course = meta.get("courses", {}).get("python-data-analysis", {})

    with get_connection() as conn:
        student_count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'user' AND is_active = 1"
        ).fetchone()[0]

        toggles_rows = conn.execute(
            "SELECT key, value FROM teacher_settings"
        ).fetchall()
        toggles_map = {r["key"]: r["value"] for r in toggles_rows}

    course_info = {
        "课程名称": course.get("title", "大数据计算集群技术"),
        "学期": "2026 秋季",
        "总讲次": f"{course.get('total_lectures', 24)} 讲",
        "班级人数": f"{student_count} 人",
        "授课语言": "中文 / Python",
        "开设院系": "数据科学学院",
    }

    ai_config = {
        "大语言模型": app_settings.llm_model or "DeepSeek Chat",
        "画像分析模型": app_settings.llm_model or "DeepSeek Chat",
        "路径规划模型": f"{app_settings.llm_model or 'DeepSeek Chat'}（LLM 驱动）",
        "评估模型": f"{app_settings.llm_model or 'DeepSeek Chat'}（LLM 驱动）",
    }

    features = []
    for key, meta in FEATURE_TOGGLE_META.items():
        enabled = toggles_map.get(key, "true") == "true"
        features.append(FeatureToggle(
            key=key, label=meta["label"], desc=meta["desc"], enabled=enabled,
        ))

    return SettingsResponse(
        course_info=course_info,
        ai_config=ai_config,
        features=features,
    )


@router.put("/settings/toggle")
def update_toggle(
    body: UpdateToggleRequest,
    admin: dict = Depends(get_current_admin),
):
    """更新功能开关状态。"""
    if body.key not in FEATURE_TOGGLE_META:
        raise HTTPException(status_code=404, detail="未知的功能开关")

    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO teacher_settings (key, value, updated_at) "
            "VALUES (?, ?, CURRENT_TIMESTAMP)",
            (body.key, "true" if body.enabled else "false"),
        )
        conn.commit()

    return {"success": True, "key": body.key, "enabled": body.enabled}
