"""评估智能体 - LLM 驱动的智能学习评估，支持 SQLite 持久化。"""
import asyncio
import json
import os
from ..core.event_bus import event_bus, Event
from ..core.database import get_connection
from ..core.llm import get_llm_client
from ..core.config import settings
from ..models.profile import DOMAIN_LABEL_TO_KEY, update_domain_skill, get_profile
from typing import Dict, Any

DEFAULT_MASTERY = {
    "Python基础": 0.0, "NumPy": 0.0, "Pandas": 0.0,
    "数据清洗": 0.0, "可视化": 0.0, "数据分析实战": 0.0,
}

ASSESS_SYSTEM_PROMPT = """你是 LearnWeave 的学习评估专家。根据学生的答题情况评估其对知识点的掌握度。

评估原则：
- 不是简单的"答对加分、答错扣分"，而是综合分析
- 考虑题目难度：简单题答对应小幅加分，难题答对应大幅加分
- 考虑答题趋势：连续答对说明真正掌握，偶然答错不代表退步
- 知识点关联：某知识点提升可能带动相关知识点的提升
- 输出新的掌握度分数（0.0-1.0）

输出 JSON：
{
  "topic_mastery": {"NumPy": 0.0, "Pandas": 0.0},
  "assessment_note": "评估说明（20-30字）",
  "weak_topics": ["数据清洗"],
  "strong_topics": ["Python基础"],
  "suggestion": "学习建议（30-50字）"
}"""


class AssessmentAgent:
    """LLM 驱动的评估智能体。

    不再使用硬编码 +0.03/-0.05，而是交由 LLM 综合分析
    题目难度、答题趋势、知识关联，给出更合理的掌握度评估。
    LLM 不可用时回退到规则计算。
    """

    def __init__(self):
        self.name = "评估智能体"
        self.llm = get_llm_client()
        self.mastery_data = self._load_mastery()
        self._ensure_table()
        # 记录最近答题历史供 LLM 分析趋势
        self._quiz_history: list = []
        # P3: 加载知识点 → 技能域映射（供 topic → domain_skill 转换）
        self._domain_map = self._load_domain_map()
        event_bus.subscribe("QUIZ_SUBMITTED", self.on_quiz_submitted)
        event_bus.subscribe("LAB_COMPLETED", self.on_lab_completed)
        event_bus.subscribe("LECTURE_COMPLETED", self.on_lecture_completed)

    # ---- P3: 领域技能映射 ----

    def _load_domain_map(self) -> dict:
        """从 knowledge_points.json 建立 topic 关键词 → 英文 skill key 映射。

        返回 {keyword_lower: skill_key}，keyword 来自知识点的 title 和 knowledge_points 标签。
        """
        domain_map: dict = {}
        kp_path = os.path.join(str(settings.kb_path), "knowledge_points.json")
        try:
            with open(kp_path, encoding="utf-8") as f:
                points = json.load(f)
            # 第一遍：加载 title + knowledge_point 标签（细粒度）
            for kp in points:
                domain_cn = kp.get("skill_domain", "")
                skill_key = DOMAIN_LABEL_TO_KEY.get(domain_cn)
                if not skill_key:
                    continue
                title = (kp.get("title") or "").lower()
                if title:
                    domain_map[title] = skill_key
                for tag in (kp.get("knowledge_points") or []):
                    domain_map[str(tag).lower()] = skill_key
            # 第二遍：加载技能域名（粗粒度，覆盖标签，保证 "Pandas"/"数据清洗" 等域名优先）
            for kp in points:
                domain_cn = kp.get("skill_domain", "")
                skill_key = DOMAIN_LABEL_TO_KEY.get(domain_cn)
                if domain_cn and skill_key:
                    domain_map[domain_cn.lower()] = skill_key
        except Exception as e:
            print(f"[AssessmentAgent] 加载领域技能映射失败: {e}")
        return domain_map

    def _topic_to_skill_key(self, topic: str) -> str | None:
        """把 topic（中文主题）映射到领域技能 key。未命中返回 None。"""
        t = (topic or "").lower()
        if not t:
            return None
        # 精确匹配 title
        if t in self._domain_map:
            return self._domain_map[t]
        # 关键词子串匹配（按最长关键词优先）
        best = None
        for kw, key in self._domain_map.items():
            if kw and kw in t:
                if best is None or len(kw) > len(best[0]):
                    best = (kw, key)
        return best[1] if best else None

    # ---- LLM 评估 ----

    async def _llm_assess(self, topic: str, correct: bool, difficulty: str,
                          old_mastery: float) -> float | None:
        """用 LLM 综合分析给出新掌握度。失败返回 None。"""
        # 最近该主题的答题趋势
        recent = [r for r in self._quiz_history[-10:] if r["topic"] == topic]
        trend_desc = []
        for r in recent[-5:]:
            trend_desc.append(
                f"{'[OK]' if r['correct'] else '[X]'} {r['difficulty']} 难度"
            )
        trend_text = " → ".join(trend_desc) if trend_desc else "首次答题"

        prompt = f"""评估学生的掌握度变化。

知识点：{topic}
当前掌握度：{old_mastery:.0%}
本次答题：{'正确' if correct else '错误'}（{difficulty} 难度）
最近趋势：{trend_text}
当前全部掌握度：{json.dumps(self.mastery_data, ensure_ascii=False)}

请输出新掌握度（JSON 格式）：
{{"{topic}": 0.85, "note": "简短评估说明"}}
只输出 JSON。"""

        try:
            raw = await self.llm.chat(
                [{"role": "system", "content": ASSESS_SYSTEM_PROMPT},
                 {"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=300,
            )
            # 提取 JSON
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            import re
            m = re.search(r'\{[^{}]*\}', raw)
            if m:
                data = json.loads(m.group())
                return float(data.get(topic, old_mastery))
        except Exception as e:
            print(f"[AssessmentAgent] LLM 评估失败: {e}")
        return None

    # ---- 持久化 ----

    def _ensure_table(self):
        """确保 mastery 表存在。"""
        try:
            conn = get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topic_mastery (
                    topic TEXT PRIMARY KEY,
                    mastery REAL NOT NULL DEFAULT 0.7,
                    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            conn.commit()
        except Exception as e:
            print(f"[AssessmentAgent] 建表失败: {e}")

    def _load_mastery(self) -> Dict[str, float]:
        """从 SQLite 加载掌握度数据。"""
        try:
            conn = get_connection()
            rows = conn.execute(
                "SELECT topic, mastery FROM topic_mastery"
            ).fetchall()
            if rows:
                data = {row[0]: row[1] for row in rows}
                print(f"[AssessmentAgent] 从数据库加载 {len(data)} 个知识点掌握度")
                return data
        except Exception as e:
            print(f"[AssessmentAgent] 加载掌握度失败，使用默认值: {e}")
        return dict(DEFAULT_MASTERY)

    def _save_mastery(self, topic: str, mastery: float):
        """持久化单个知识点的掌握度。"""
        try:
            conn = get_connection()
            conn.execute(
                """INSERT INTO topic_mastery (topic, mastery, updated_at)
                   VALUES (?, ?, datetime('now', 'localtime'))
                   ON CONFLICT(topic) DO UPDATE SET
                   mastery = excluded.mastery,
                   updated_at = datetime('now', 'localtime')""",
                (topic, mastery)
            )
            conn.commit()
        except Exception as e:
            print(f"[AssessmentAgent] 保存掌握度失败 ({topic}): {e}")
    
    # [OK] 新增同步评估方法（供 orchestrator 调用）
    def assess(self, profile: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        同步评估用户画像，返回评估结果
        :param profile: 用户画像数据（如兴趣、强弱项）
        :param context: 额外上下文，如 {"topic": "Pandas 数据处理", "score": 80}
        :return: 评估结果字典
        """
        if context is None:
            context = {}

        topic = context.get("topic", "Pandas")
        score = context.get("score", 0)

        # 基于当前掌握度数据生成评估
        topic_mastery = self.mastery_data.get(topic, 0.7)

        # 如果传入了具体分数，则优先使用
        if score > 0:
            topic_mastery = score / 100.0  # 假设传入的是百分制

        # 整体掌握度
        overall = sum(self.mastery_data.values()) / len(self.mastery_data)

        # 生成建议
        suggestions = []
        weak_topics = [k for k, v in self.mastery_data.items() if v < 0.6]
        if weak_topics:
            suggestions.append(f"加强学习：{', '.join(weak_topics)}")
        if topic_mastery < 0.6:
            suggestions.append(f"重点关注：{topic} 知识点，当前掌握度 {topic_mastery*100:.0f}%")
        elif topic_mastery >= 0.8:
            suggestions.append(f"{topic} 掌握良好，可以进入更高级主题")
        else:
            suggestions.append(f"{topic} 掌握一般，建议多做练习")

        if not suggestions:
            suggestions.append("继续按当前进度学习")

        return {
            "level": "advanced" if overall > 0.8 else "intermediate" if overall > 0.6 else "beginner",
            "score": int(topic_mastery * 100),
            "overall_mastery": int(overall * 100),
            "suggestions": suggestions,
            "weak_topics": weak_topics,
            "strong_topics": [k for k, v in self.mastery_data.items() if v >= 0.8]
        }

    async def on_quiz_submitted(self, event: Event):
        """LLM 驱动的答题评估"""
        topic = event.data.get("topic", "Pandas")
        correct = event.data.get("correct", False)
        difficulty = event.data.get("difficulty", "medium")
        user_id = event.data.get("user_id", 1)
        score = event.data.get("score")
        total = event.data.get("total", 1)

        # 记录历史（保留最近 20 条）
        self._quiz_history.append({
            "topic": topic, "correct": correct, "difficulty": difficulty
        })
        if len(self._quiz_history) > 20:
            self._quiz_history = self._quiz_history[-20:]

        old_mastery = self.mastery_data.get(topic, 0.70)

        # 尝试 LLM 评估
        new_mastery = await self._llm_assess(topic, correct, difficulty, old_mastery)

        # LLM 失败时回退规则
        if new_mastery is None:
            if correct:
                diff_bonus = {"easy": 0.02, "medium": 0.04, "hard": 0.07}
                new_mastery = min(1.0, old_mastery + diff_bonus.get(difficulty, 0.03))
            else:
                diff_penalty = {"easy": 0.06, "medium": 0.03, "hard": 0.01}
                new_mastery = max(0.0, old_mastery - diff_penalty.get(difficulty, 0.05))

        self.mastery_data[topic] = new_mastery
        self._save_mastery(topic, new_mastery)

        # P3: 同步更新领域技能画像（可解释公式）
        # 答对：按难度加分（简单 +10 / 中等 +15 / 困难 +20）
        # 答错：按难度扣分（简单 -15 / 中等 -10 / 困难 -5，难题答错扣分少）
        skill_key = self._topic_to_skill_key(topic)
        domain_score = None
        if skill_key:
            # 优先用 score 比例计算 delta（更精确），否则回退 correct + difficulty
            if score is not None and total > 0:
                ratio = score / total
                if ratio >= 0.8:
                    delta = 20
                elif ratio >= 0.6:
                    delta = 10
                elif ratio >= 0.4:
                    delta = -15
                else:
                    delta = -25
            elif correct:
                delta = {"easy": 10, "medium": 15, "hard": 20}.get(difficulty, 10)
            else:
                delta = -{"easy": 15, "medium": 10, "hard": 5}.get(difficulty, 10)
            try:
                result = update_domain_skill(user_id, skill_key, delta, reason="答题正确" if correct else "答题错误")
                domain_score = result["new"]
            except Exception as e:
                print(f"[AssessmentAgent] 更新领域技能失败: {e}")

        await event_bus.publish(
            "MASTERY_CHANGED",
            {
                "topic": topic,
                "old_mastery": old_mastery,
                "new_mastery": new_mastery,
                "change": new_mastery - old_mastery,
                "user_id": user_id,
                "overall_mastery": sum(self.mastery_data.values()) / len(self.mastery_data)
            },
            source=self.name
        )

        # 检测薄弱点（基于领域技能分数 0-100；映射不到技能域时回退 topic_mastery）
        if domain_score is not None and domain_score < 60:
            await event_bus.publish(
                "WEAKNESS_DETECTED",
                {
                    "topic": topic,
                    "skill_key": skill_key,
                    "mastery": domain_score,
                    "user_id": user_id
                },
                source=self.name
            )
        elif domain_score is None and new_mastery < 0.60:
            await event_bus.publish(
                "WEAKNESS_DETECTED",
                {
                    "topic": topic,
                    "mastery": round(new_mastery * 100),
                    "user_id": user_id
                },
                source=self.name
            )
    
    async def on_lab_completed(self, event: Event):
        """处理实验完成，并按实训结果更新领域技能画像。"""
        lab_name = event.data.get("lab_name", "Pandas 数据处理实战")
        topic = event.data.get("topic", lab_name)
        user_id = event.data.get("user_id", 1)
        score = event.data.get("score")  # 实训批改分数 0-100，可选

        # P3: 实训 → 领域技能更新（可解释公式）
        # score >= 60 加分（每超 1 分 +0.5，封顶 +20）
        # score <  60 扣分（每低 1 分 -0.5，封顶 -20）
        skill_key = self._topic_to_skill_key(topic)
        if skill_key and isinstance(score, (int, float)):
            delta = max(-20, min(20, int((score - 60) / 2)))
            if delta != 0:
                try:
                    update_domain_skill(user_id, skill_key, delta, reason=f"实训{score}分")
                except Exception as e:
                    print(f"[AssessmentAgent] 更新领域技能失败: {e}")

        # 触发评估
        await event_bus.publish(
            "STEP_COMPLETED",
            {
                "step_id": 3,
                "step_name": "实践实验",
                "lab_name": lab_name,
                "user_id": user_id
            },
            source=self.name
        )
    
    async def on_lecture_completed(self, event: Event):
        """处理讲次完成"""
        lecture_id = event.data.get("lecture_id", 8)
        user_id = event.data.get("user_id", 1)
        
        await event_bus.publish(
            "STEP_COMPLETED",
            {
                "step_id": 2,
                "step_name": "学习讲次",
                "lecture_id": lecture_id,
                "user_id": user_id
            },
            source=self.name
        )

    def assess(self, profile: list, context: dict = None) -> dict:
        """同步评估方法 — 供 LangGraph 编排器调用

        Args:
            profile: 6 维画像分数列表
            context: 额外上下文（topic, quiz_results 等）

        Returns:
            评估报告 dict
        """
        dim_names = ["理论基础", "编程能力", "实践操作", "问题排查", "数据思维", "自学能力"]
        scored = [s for s in profile if s > 0]
        mastery = round(sum(scored) / len(scored)) if scored else 0
        avg_mastery = sum(self.mastery_data.values()) / len(self.mastery_data)

        weak_points = []
        for i, score in enumerate(profile):
            if score > 0 and score < 60:
                weak_points.append({
                    "name": dim_names[i],
                    "score": score,
                    "action": f"建议重点学习{dim_names[i]}相关课程内容",
                })

        recommendations = []
        if weak_points:
            recommendations.append(f"优先攻克「{weak_points[0]['name']}」(当前{weak_points[0]['score']}分)")
        recommendations.append(f"当前综合掌握度 {mastery}%，实验掌握度 {round(avg_mastery * 100)}%")

        return {
            "mastery": mastery,
            "experiment_mastery": round(avg_mastery * 100),
            "weak_points": weak_points,
            "recommendations": recommendations,
            "knowledge_points": [
                {"name": dim_names[i], "mastery": profile[i]}
                for i in range(len(profile))
            ],
        }


def get_assessment_agent() -> AssessmentAgent:
    return AssessmentAgent()