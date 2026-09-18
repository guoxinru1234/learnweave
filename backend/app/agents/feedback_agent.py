"""FeedbackAgent — 学习交互反馈处理 + 动态难度决策。

策略:
  - 正确率 <60%  → 降维解释 + 基础练习
  - 60%-85%      → 保持难度 + 针对性练习
  - >85%         → 进阶挑战
  - 连续≥3次错   → 增加提示 + 分步示例
  - 连续≥3次对   → 减少重复基础内容
"""
import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "learnmate.db"


def _db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


class FeedbackAgent:
    """学习交互反馈 Agent — 接收答题数据，更新掌握度，输出决策建议"""

    def process(self, learner_id: int, resource_id: str = "",
                question_id: str = "", answer: str = "",
                is_correct: bool = False, attempt_count: int = 1,
                time_spent_seconds: int = 0, hint_used: bool = False,
                topic: str = "") -> dict:
        """处理一次学习交互，返回掌握度更新和决策建议。

        Returns:
            {knowledge_point, recent_accuracy, mastery_update, trend,
             recommended_action, decision_reason, next_resource_difficulty, next_task_type}
        """
        # 保存交互记录
        conn = _db()
        conn.execute("""CREATE TABLE IF NOT EXISTS learning_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            learner_id INTEGER, resource_id TEXT, question_id TEXT,
            answer TEXT, is_correct INTEGER, attempt_count INTEGER,
            time_spent_seconds INTEGER, hint_used INTEGER,
            topic TEXT, created_at TEXT
        )""")
        conn.execute("""INSERT INTO learning_interactions
            (learner_id, resource_id, question_id, answer, is_correct,
             attempt_count, time_spent_seconds, hint_used, topic, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (learner_id, resource_id, question_id, answer,
             1 if is_correct else 0, attempt_count, time_spent_seconds,
             1 if hint_used else 0, topic, datetime.now(timezone.utc).isoformat()))
        conn.commit()

        # 分析最近答题情况
        recent = conn.execute(
            "SELECT is_correct, hint_used, attempt_count FROM learning_interactions "
            "WHERE learner_id=? AND topic=? ORDER BY id DESC LIMIT 10",
            (learner_id, topic)
        ).fetchall()
        total = len(recent)
        correct = sum(1 for r in recent if r["is_correct"])
        accuracy = round(correct / max(total, 1) * 100, 1)

        # 连续答错/答对检测
        streak_wrong = 0
        streak_correct = 0
        for r in recent:
            if r["is_correct"]:
                streak_correct += 1
                streak_wrong = 0
            else:
                streak_wrong += 1
                streak_correct = 0
            if streak_wrong >= 3 or streak_correct >= 3:
                break

        # 趋势
        if total >= 3:
            first_half = sum(1 for r in recent[:total//2] if r["is_correct"]) / max(total//2, 1)
            second_half = sum(1 for r in recent[total//2:] if r["is_correct"]) / max(total - total//2, 1)
            trend = "improving" if second_half > first_half else ("declining" if second_half < first_half else "stable")
        else:
            trend = "insufficient_data"

        # 掌握度更新
        hint_penalty = 0.05 if hint_used else 0
        mastery_delta = 0
        if is_correct:
            mastery_delta = 5 - hint_penalty * 5
        else:
            mastery_delta = -5 - (attempt_count - 1) * 2

        # 决策
        if accuracy < 60:
            action = "降维解释 + 基础练习"
            reason = f"最近正确率{accuracy}%低于60%阈值"
            next_difficulty = "basic"
            next_task = "基础题 + 分步代码示例"
        elif accuracy > 85:
            action = "进阶挑战"
            reason = f"最近正确率{accuracy}%高于85%阈值"
            next_difficulty = "advanced"
            next_task = "进阶综合题 + 实战项目"
        else:
            action = "保持难度 + 针对性练习"
            reason = f"最近正确率{accuracy}%在60%-85%区间"
            next_difficulty = "intermediate"
            next_task = "混合练习 + 知识点专项"

        if streak_wrong >= 3:
            action += " + 增加提示和分步示例"
            reason += f"；连续{streak_wrong}次答错"
            next_difficulty = "basic"
        if streak_correct >= 3:
            action += "；减少重复基础内容"
            reason += f"；连续{streak_correct}次答对"

        conn.close()

        return {
            "knowledge_point": topic,
            "recent_accuracy": accuracy,
            "mastery_update": round(mastery_delta, 1),
            "trend": trend,
            "recommended_action": action,
            "decision_reason": reason,
            "next_resource_difficulty": next_difficulty,
            "next_task_type": next_task,
        }


def get_feedback_agent() -> FeedbackAgent:
    return FeedbackAgent()
