"""DiagnosisReport — 聚合多数据源生成学情诊断报告。

数据来源: learner_profiles, topic_mastery, quiz_attempts, learning_interactions, learning_records.
resource_match 使用确定性计算规则，不依赖 LLM。
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

DB_PATH = Path(__file__).parent.parent.parent / "data" / "learnmate.db"

DIM_LABELS = ["theoretical_basis", "coding_ability", "practical_ops",
              "troubleshooting", "data_thinking", "self_learning"]
DIM_NAMES = ["理论基础", "编程能力", "实践操作", "问题排查", "数据思维", "自学能力"]

TOPICS = ["Python基础", "NumPy", "Pandas", "数据清洗", "数据可视化",
          "环境搭建", "函数编程", "SQL", "ETL", "机器学习"]


def _db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def generate_report(learner_id: int) -> dict:
    """生成学情诊断报告。无数据时返回稳定空结构。"""
    conn = _db()

    # 1. 画像数据
    profile = conn.execute(
        "SELECT * FROM learner_profiles WHERE user_id=?", (learner_id,)
    ).fetchone()

    # 2. 知识点掌握度（从 topic_mastery + quiz_attempts 推导）
    topic_scores = _get_topic_mastery(conn, learner_id)

    # 3. 交互反馈历史
    interactions = conn.execute(
        "SELECT topic, is_correct, attempt_count, hint_used, created_at "
        "FROM learning_interactions WHERE learner_id=? ORDER BY id DESC LIMIT 30",
        (learner_id,)
    ).fetchall()

    # 4. 学习记录
    records = conn.execute(
        "SELECT date, study_minutes, completed_lectures, accuracy "
        "FROM learning_records WHERE user_id=? ORDER BY date DESC LIMIT 10",
        (learner_id,)
    ).fetchall()

    conn.close()

    # 构建报告
    knowledge_mastery = []
    knowledge_gaps = []
    mastered_points = []
    for topic in TOPICS:
        data = topic_scores.get(topic, {"correct": 0, "total": 0, "avg_attempts": 1})
        mastery = _calc_mastery(data)
        evidence = f"答题{data['total']}次, 正确{data['correct']}次, 均尝试{data['avg_attempts']:.1f}次"
        entry = {"knowledge_point": topic, "mastery": mastery, "evidence": evidence}
        knowledge_mastery.append(entry)
        if mastery < 50:
            knowledge_gaps.append(entry)
        elif mastery >= 75:
            mastered_points.append(topic)

    # resource_match: 确定性计算
    dim_scores = {}
    if profile:
        for d in DIM_LABELS:
            dim_scores[d] = profile[d] if profile[d] is not None else 0
    avg_score = round(sum(dim_scores.values()) / len(dim_scores)) if dim_scores else 30
    resource_match = []
    resources = [
        {"name": "基础讲义", "difficulty": "basic", "points": ["Python基础", "环境搭建"]},
        {"name": "NumPy教程", "difficulty": "basic", "points": ["NumPy"]},
        {"name": "Pandas实战", "difficulty": "intermediate", "points": ["Pandas", "数据清洗"]},
        {"name": "可视化指南", "difficulty": "intermediate", "points": ["数据可视化"]},
        {"name": "机器学习入门", "difficulty": "advanced", "points": ["机器学习"]},
        {"name": "ETL项目", "difficulty": "advanced", "points": ["ETL", "SQL"]},
    ]
    for res in resources:
        covered = set(res["points"]) & set(mastered_points)
        gap_overlap = set(res["points"]) & set(g["knowledge_point"] for g in knowledge_gaps)
        # match_score = 基础匹配 + 已掌握加分 - 薄弱冲突扣分
        base = 50
        base += len(covered) * 15
        base -= len(gap_overlap) * 10
        if avg_score < 35:
            base += 10 if res["difficulty"] == "basic" else 0
        elif avg_score > 70:
            base += 10 if res["difficulty"] == "advanced" else 0
        match_score = min(100, max(0, base))
        resource_match.append({
            "name": res["name"], "difficulty": res["difficulty"],
            "match_score": match_score, "covered_points": list(covered),
        })

    # 学习路径
    learning_path = [
        {"order": 1, "topic": "Python基础", "prerequisite": None, "status": "completed" if topic_scores.get("Python基础", {}).get("total", 0) >= 3 else "pending"},
        {"order": 2, "topic": "NumPy", "prerequisite": "Python基础", "status": "completed" if topic_scores.get("NumPy", {}).get("total", 0) >= 3 else "pending"},
        {"order": 3, "topic": "Pandas", "prerequisite": "NumPy", "status": "ready" if topic_scores.get("NumPy", {}).get("total", 0) >= 3 else "locked"},
        {"order": 4, "topic": "数据清洗", "prerequisite": "Pandas", "status": "ready" if topic_scores.get("Pandas", {}).get("total", 0) >= 3 else "locked"},
        {"order": 5, "topic": "数据可视化", "prerequisite": "Pandas", "status": "locked"},
        {"order": 6, "topic": "机器学习", "prerequisite": "数据清洗", "status": "locked"},
    ]

    # 反馈历史
    recent_feedback = []
    for row in interactions[:10]:
        recent_feedback.append({
            "topic": row["topic"], "is_correct": bool(row["is_correct"]),
            "attempt_count": row["attempt_count"], "hint_used": bool(row["hint_used"]),
            "timestamp": row["created_at"],
        })

    # 难度历史
    difficulty_history = []
    for r in records:
        difficulty_history.append({
            "date": r["date"], "study_minutes": r["study_minutes"],
            "accuracy": r["accuracy"] or 0,
        })

    # 决策历史（汇总）
    decision_history = []
    if knowledge_gaps:
        decision_history.append(f"薄弱点: {', '.join(g['knowledge_point'] for g in knowledge_gaps[:3])}")
    if mastered_points:
        decision_history.append(f"已掌握: {', '.join(mastered_points[:3])}")
    top_resource = max(resource_match, key=lambda r: r["match_score"]) if resource_match else None
    if top_resource:
        decision_history.append(f"推荐资源: {top_resource['name']} (匹配度{top_resource['match_score']})")

    return {
        "learner_id": learner_id,
        "knowledge_mastery": knowledge_mastery,
        "knowledge_gaps": knowledge_gaps,
        "mastered_points": mastered_points,
        "resource_match": resource_match,
        "learning_path": learning_path,
        "recent_feedback": recent_feedback,
        "difficulty_history": difficulty_history,
        "decision_history": decision_history,
        "profile_score": avg_score,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": {
            "has_profile": profile is not None,
            "interactions_count": len(interactions),
            "records_count": len(records),
        },
    }


def _get_topic_mastery(conn, learner_id: int) -> dict:
    rows = conn.execute(
        "SELECT topic, is_correct, attempt_count FROM learning_interactions WHERE learner_id=?",
        (learner_id,)
    ).fetchall()
    result: Dict[str, dict] = {}
    for r in rows:
        t = r["topic"] or "综合"
        if t not in result:
            result[t] = {"correct": 0, "total": 0, "attempts": 0}
        result[t]["total"] += 1
        result[t]["attempts"] += (r["attempt_count"] or 1)
        if r["is_correct"]:
            result[t]["correct"] += 1
    for t in result:
        result[t]["avg_attempts"] = result[t]["attempts"] / max(result[t]["total"], 1)
    return result


def _calc_mastery(data: dict) -> int:
    if data["total"] == 0:
        return 0
    base = round(data["correct"] / data["total"] * 100)
    # 多次尝试才答对 → 扣分
    penalty = max(0, (data["avg_attempts"] - 1) * 10)
    return max(0, min(100, base - int(penalty)))
