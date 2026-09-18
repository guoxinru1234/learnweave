"""学情画像数据模型 — 6 维能力雷达图 + 偏好 + 对话状态"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json
import sqlite3
import os


# ===== SQLite 持久化 =====

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "learnmate.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table():
    """确保 profile 表存在"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learner_profiles (
            user_id INTEGER PRIMARY KEY,
            major_background TEXT DEFAULT '',
            theoretical_basis INTEGER DEFAULT 0,
            coding_ability INTEGER DEFAULT 0,
            practical_ops INTEGER DEFAULT 0,
            troubleshooting INTEGER DEFAULT 0,
            data_thinking INTEGER DEFAULT 0,
            self_learning INTEGER DEFAULT 0,
            theory_description TEXT DEFAULT '',
            coding_description TEXT DEFAULT '',
            practice_description TEXT DEFAULT '',
            debug_description TEXT DEFAULT '',
            data_description TEXT DEFAULT '',
            self_learning_description TEXT DEFAULT '',
            cognitive_style TEXT DEFAULT '',
            learning_pace TEXT DEFAULT '',
            learning_motivation TEXT DEFAULT '',
            dialogue_step INTEGER DEFAULT 0,
            dialogue_completed INTEGER DEFAULT 0,
            dialogue_history TEXT DEFAULT '[]',
            domain_skills TEXT DEFAULT '{}',
            updated_at TEXT DEFAULT ''
        )
    """)
    # 兼容旧表：若已存在但缺 domain_skills 列，则补加
    try:
        conn.execute("ALTER TABLE learner_profiles ADD COLUMN domain_skills TEXT DEFAULT '{}'")
    except Exception:
        pass
    conn.commit()
    conn.close()


# 模块加载时建表
_ensure_table()


# ===== 维度元数据 =====

DIMENSION_KEYS = [
    "theoretical_basis", "coding_ability", "practical_ops",
    "troubleshooting", "data_thinking", "self_learning",
]

DIMENSION_LABELS: dict[str, str] = {
    "theoretical_basis": "理论基础",
    "coding_ability": "编程能力",
    "practical_ops": "实践操作",
    "troubleshooting": "问题排查",
    "data_thinking": "数据思维",
    "self_learning": "自学能力",
}

DESC_KEY_MAP: dict[str, str] = {
    "theoretical_basis": "theory_description",
    "coding_ability": "coding_description",
    "practical_ops": "practice_description",
    "troubleshooting": "debug_description",
    "data_thinking": "data_description",
    "self_learning": "self_learning_description",
}


# ===== P3: 领域技能画像（10 技能域，与 knowledge-base/skill_tree.json 一致） =====

DOMAIN_SKILL_KEYS = [
    "python_basic", "numpy", "pandas", "data_cleaning",
    "visualization", "etl", "sql", "statistics",
    "comprehensive_analysis", "performance",
]

# 英文 key → 中文技能域名（与 skill_tree.json 的技能域一一对应）
DOMAIN_SKILL_LABELS: dict[str, str] = {
    "python_basic": "Python基础",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "data_cleaning": "数据清洗",
    "visualization": "数据可视化",
    "etl": "ETL数据管道",
    "sql": "SQL与数据库",
    "statistics": "统计分析",
    "comprehensive_analysis": "综合数据分析",
    "performance": "性能优化与部署",
}

# 中文技能域名 → 英文 key（反向映射，供知识库 skill_domain 转换用）
DOMAIN_LABEL_TO_KEY: dict[str, str] = {v: k for k, v in DOMAIN_SKILL_LABELS.items()}


@dataclass
class LearnerProfile:
    """学情画像 — 6 维纯能力雷达图 + 3 项学习偏好"""

    user_id: int = 1

    # ===== 专业背景（文本，不入雷达图） =====
    major_background: str = ""

    # ===== 六维能力雷达（0-100） =====
    theoretical_basis: int = 0       # 理论基础：概念原理掌握
    coding_ability: int = 0          # 编程能力：写代码/调试
    practical_ops: int = 0           # 实践操作：搭环境/用工具
    troubleshooting: int = 0         # 问题排查：报错分析/搜答案
    data_thinking: int = 0           # 数据思维：分析流程/建模
    self_learning: int = 0           # 自学能力：查文档/跟新技术/独立解决问题

    # 六维描述
    theory_description: str = ""
    coding_description: str = ""
    practice_description: str = ""
    debug_description: str = ""
    data_description: str = ""
    self_learning_description: str = ""

    # ===== 学习偏好 =====
    cognitive_style: str = ""
    learning_pace: str = ""
    learning_motivation: str = ""

    # ===== P3: 领域技能画像（10 技能域，0-100，与 P1 skill_tree 一致） =====
    domain_skills: dict = field(default_factory=dict)

    # ===== 对话状态 =====
    dialogue_step: int = 0
    dialogue_completed: bool = False
    dialogue_history: list = field(default_factory=list)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ===== 计算属性 =====

    @property
    def overall_score(self) -> int:
        scores = [getattr(self, k, 0) for k in DIMENSION_KEYS]
        valid = [s for s in scores if s > 0]
        if not valid:
            return 0
        return int(sum(valid) / len(valid))

    @property
    def weak_dimensions(self) -> list:
        dims = [(DIMENSION_LABELS[k], getattr(self, k, 0)) for k in DIMENSION_KEYS]
        return sorted(dims, key=lambda x: x[1])[:3]

    @property
    def strong_dimensions(self) -> list:
        dims = [(DIMENSION_LABELS[k], getattr(self, k, 0)) for k in DIMENSION_KEYS]
        return sorted(dims, key=lambda x: x[1], reverse=True)[:3]

    # ===== P3: 领域技能薄弱点/强项（0-100，中文标签） =====

    @property
    def domain_weak_skills(self) -> list:
        items = [(DOMAIN_SKILL_LABELS.get(k, k), v) for k, v in self.domain_skills.items()]
        return sorted(items, key=lambda x: x[1])[:3]

    @property
    def domain_strong_skills(self) -> list:
        items = [(DOMAIN_SKILL_LABELS.get(k, k), v) for k, v in self.domain_skills.items()]
        return sorted(items, key=lambda x: x[1], reverse=True)[:3]

    @property
    def completion_percentage(self) -> int:
        scored = sum(1 for k in DIMENSION_KEYS if getattr(self, k, 0) > 0)
        return min(100, int(scored / len(DIMENSION_KEYS) * 100))


# ===== 持久化存取 =====

def _row_to_profile(row) -> LearnerProfile:
    """将 SQLite 行转为 LearnerProfile"""
    history_raw = row["dialogue_history"] if row["dialogue_history"] else "[]"
    try:
        history = json.loads(history_raw)
    except json.JSONDecodeError:
        history = []

    domain_raw = row["domain_skills"] if "domain_skills" in row.keys() else "{}"
    try:
        domain_skills = json.loads(domain_raw) if domain_raw else {}
    except json.JSONDecodeError:
        domain_skills = {}

    return LearnerProfile(
        user_id=row["user_id"],
        major_background=row["major_background"] or "",
        theoretical_basis=row["theoretical_basis"] or 0,
        coding_ability=row["coding_ability"] or 0,
        practical_ops=row["practical_ops"] or 0,
        troubleshooting=row["troubleshooting"] or 0,
        data_thinking=row["data_thinking"] or 0,
        self_learning=row["self_learning"] or 0,
        theory_description=row["theory_description"] or "",
        coding_description=row["coding_description"] or "",
        practice_description=row["practice_description"] or "",
        debug_description=row["debug_description"] or "",
        data_description=row["data_description"] or "",
        self_learning_description=row["self_learning_description"] or "",
        cognitive_style=row["cognitive_style"] or "",
        learning_pace=row["learning_pace"] or "",
        learning_motivation=row["learning_motivation"] or "",
        domain_skills=domain_skills,
        dialogue_step=row["dialogue_step"] or 0,
        dialogue_completed=bool(row["dialogue_completed"]),
        dialogue_history=history,
        updated_at=row["updated_at"] or datetime.now().isoformat(),
    )


def get_profile(user_id: int = 1) -> LearnerProfile:
    """从 SQLite 读取画像，不存在则创建空画像"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM learner_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return LearnerProfile(user_id=user_id)
    return _row_to_profile(row)


def save_profile(profile: LearnerProfile):
    """保存画像到 SQLite（upsert）"""
    profile.updated_at = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO learner_profiles (
            user_id, major_background,
            theoretical_basis, coding_ability, practical_ops,
            troubleshooting, data_thinking, self_learning,
            theory_description, coding_description, practice_description,
            debug_description, data_description, self_learning_description,
            cognitive_style, learning_pace, learning_motivation,
            dialogue_step, dialogue_completed, dialogue_history, domain_skills, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        profile.user_id, profile.major_background,
        profile.theoretical_basis, profile.coding_ability, profile.practical_ops,
        profile.troubleshooting, profile.data_thinking, profile.self_learning,
        profile.theory_description, profile.coding_description, profile.practice_description,
        profile.debug_description, profile.data_description, profile.self_learning_description,
        profile.cognitive_style, profile.learning_pace, profile.learning_motivation,
        profile.dialogue_step, int(profile.dialogue_completed),
        json.dumps(profile.dialogue_history, ensure_ascii=False),
        json.dumps(profile.domain_skills, ensure_ascii=False),
        profile.updated_at,
    ))
    conn.commit()
    conn.close()


# ===== P3: 领域技能画像更新函数（可解释的更新公式） =====

def set_initial_domain_skills(user_id: int, scores: dict) -> LearnerProfile:
    """从初始测试设置领域技能画像。

    例: set_initial_domain_skills(1, {"pandas": 80, "python_basic": 85})
    只接受 DOMAIN_SKILL_KEYS 中的技能，分数截断到 0-100。
    """
    profile = get_profile(user_id)
    for key in DOMAIN_SKILL_KEYS:
        if key in scores:
            profile.domain_skills[key] = max(0, min(100, int(scores[key])))
    save_profile(profile)
    return profile


def _ensure_domain_changes_table():
    """确保领域技能变化记录表存在。"""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS domain_skill_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_key TEXT,
            old INTEGER,
            new INTEGER,
            delta INTEGER,
            reason TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()


def update_domain_skill(user_id: int, skill_key: str, delta: int, reason: str = "") -> dict:
    """更新单个领域技能分数（可解释的增量更新）。

    规则：新分数 = clamp(old + delta, 0, 100)。
    若技能此前无记录，从 50（中性）起步。
    同时记录变化到 domain_skill_changes（供"随学随新"展示）。
    返回更新前后的分数。
    """
    if skill_key not in DOMAIN_SKILL_KEYS:
        raise ValueError(f"未知技能域: {skill_key}，合法值为 {DOMAIN_SKILL_KEYS}")
    profile = get_profile(user_id)
    old = profile.domain_skills.get(skill_key, 50)
    new = max(0, min(100, old + delta))
    profile.domain_skills[skill_key] = new
    save_profile(profile)
    # 记录变化
    try:
        _ensure_domain_changes_table()
        conn = _get_conn()
        conn.execute(
            "INSERT INTO domain_skill_changes (user_id, skill_key, old, new, delta, reason) VALUES (?,?,?,?,?,?)",
            (user_id, skill_key, old, new, delta, reason),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[profile] 记录领域技能变化失败: {e}")
    return {"skill": skill_key, "old": old, "new": new, "delta": delta}


def get_domain_skill_changes(user_id: int, limit: int = 10) -> list:
    """获取领域技能的最近变化记录（供"随学随新"展示）。"""
    try:
        _ensure_domain_changes_table()
        conn = _get_conn()
        rows = conn.execute(
            "SELECT skill_key, old, new, delta, reason FROM domain_skill_changes "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit),
        ).fetchall()
        conn.close()
        return [
            {"skill": r["skill_key"], "label": DOMAIN_SKILL_LABELS.get(r["skill_key"], r["skill_key"]),
             "old": r["old"], "new": r["new"], "delta": r["delta"], "reason": r["reason"]}
            for r in rows
        ]
    except Exception as e:
        print(f"[profile] 读取领域技能变化失败: {e}")
        return []


# 向后兼容：保留内存缓存的引用（router/reset 使用）
_profile_store: dict[int, LearnerProfile] = {}
