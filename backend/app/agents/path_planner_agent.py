from ..core.event_bus import event_bus, Event
from ..models.journey import get_journey, save_journey
from ..models.profile import get_profile, DOMAIN_SKILL_LABELS
from ..rag.engine import RAGEngine
from ..core.config import settings
from typing import Dict, Any

class PathPlannerAgent:
    """
    路径规划智能体 - 动态调整学习路径（基于领域技能 + 知识点前置关系）
    """

    def __init__(self):
        self.name = "路径规划智能体"
        self.rag = RAGEngine(str(settings.kb_path))
        event_bus.subscribe("WEAKNESS_DETECTED", self.on_weakness)
        event_bus.subscribe("PLAN_UPDATE_REQUESTED", self.on_plan_update)
        event_bus.subscribe("PROFILE_UPDATE_REQUESTED", self.on_profile_update)

    async def on_weakness(self, event: Event):
        """薄弱点检测时，基于领域技能 + 知识点前置关系规划补强路径。"""
        topic = event.data.get("topic")
        mastery = event.data.get("mastery")
        user_id = event.data.get("user_id", 1)

        # 1. 检索薄弱知识点
        kps = self.rag.search_knowledge_points(topic or "", top_k=1)
        kp = kps[0] if kps else None

        # 2. 读领域技能画像
        domain_skills = get_profile(user_id).domain_skills

        # 3. 生成专项路径（含前置知识，不用重新学整个技能域）
        if kp:
            prerequisites = kp.get("prerequisites", [])
            skill_domain = kp.get("skill_domain", "")
            plan = {
                "knowledge_id": kp.get("knowledge_id"),
                "skill_domain": skill_domain,
                "title": kp.get("title"),
                "source_lessons": kp.get("source_lessons", []),
                "mastery": mastery,
                "action": "专项训练",
                "prerequisites": prerequisites,
                "priority": "高" if mastery < 55 else "中",
                "reason": f"{skill_domain} 掌握度 {mastery}%，针对「{kp.get('title')}」专项补强（前置: {prerequisites or '无'}）",
            }
        else:
            # 兜底：用最低领域技能定位
            weak_skill = min(domain_skills, key=domain_skills.get, default=None) if domain_skills else None
            plan = {
                "topic": topic,
                "weak_skill": weak_skill,
                "action": "专项练习",
                "count": 3,
                "priority": "高" if mastery < 55 else "中",
                "reason": f"掌握度 {mastery}%，需要补强",
            }

        await event_bus.publish(
            "PLAN_GENERATED",
            {
                "plan": plan,
                "user_id": user_id
            },
            source=self.name
        )

    async def on_plan_update(self, event: Event):
        """更新学习路径"""
        user_id = event.data.get("user_id", 1)
        journey = get_journey(user_id)

        # 更新旅程进度
        step_id = event.data.get("completed_step")
        if step_id:
            journey.complete_step(step_id)
            save_journey(journey)

            await event_bus.publish(
                "JOURNEY_UPDATED",
                {
                    "current_step": journey.current_step_id,
                    "progress": journey.overall_progress,
                    "next_step": journey.get_next_step()
                },
                source=self.name
            )

    async def on_profile_update(self, event: Event):
        """画像更新时，调整路径"""
        # 触发画像智能体
        await event_bus.publish(
            "PROFILE_UPDATED",
            event.data,
            source=self.name
        )

def get_path_planner() -> PathPlannerAgent:
    return PathPlannerAgent()