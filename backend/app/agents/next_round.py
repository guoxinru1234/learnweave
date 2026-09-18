"""下一轮学习协调器 — 把 PathPlanner 的产出重新喂给 VerificationOrchestrator。

职责:
  - 订阅 PLAN_GENERATED 事件(由 PathPlannerAgent.on_weakness 发布),
    反查薄弱知识点 → 定位下一讲次 → 后台调用 VerificationOrchestrator 生成下一轮资源。
  - 提供 generate_next_round(user_id, ...) 供 REST 端点按需触发。

设计要点:
  - 事件链 QUIZ_SUBMITTED → ... → PLAN_GENERATED 在 await publish 内同步串行,
    因此 on_plan_generated 必须 asyncio.create_task 后台执行,避免阻塞答题请求。
  - 自动路径对同一 (user_id, lecture_num) 做冷却去重,防止连点答题触发重复昂贵生成。
"""
import asyncio
import json
import os
import time
from typing import Any, Dict, Optional

from ..core.config import settings
from ..core.event_bus import event_bus, Event
from ..models.profile import get_profile, DOMAIN_SKILL_LABELS
from ..rag.engine import RAGEngine

CACHE_DIR = "data/lecture_cache"


class NextRoundCoordinator:
    def __init__(self):
        self.name = "下一轮学习协调器"
        self.rag = RAGEngine(str(settings.kb_path))
        self._knowledge_points = self._load_knowledge_points()
        self._cooldown: dict = {}  # (user_id, lecture_num) -> 上次生成时间戳
        event_bus.subscribe("PLAN_GENERATED", self.on_plan_generated)

    # ================================================================
    # 事件入口(后台)
    # ================================================================
    async def on_plan_generated(self, event: Event):
        plan = event.data.get("plan") or {}
        user_id = event.data.get("user_id", 1)
        if not settings.learning_loop_enabled:
            return
        # 后台执行,不阻塞上游事件链(quiz.py 是 await publish 同步串行)
        asyncio.create_task(self._generate_from_plan(plan, user_id))

    async def _generate_from_plan(self, plan: dict, user_id: int):
        try:
            lecture_num = self._resolve_lecture(plan)
            if self._recently_generated(user_id, lecture_num):
                return
            # 生成开始即打标记,防止并发/连点事件在冷却判定前的竞态重复生成
            self._mark_generated(user_id, lecture_num)
            result = await self._run_generation(
                user_id, lecture_num, plan.get("title") or "", mode="review",
            )
            await event_bus.publish(
                "NEXT_ROUND_READY",
                {
                    "user_id": user_id,
                    "course_id": result.get("course_id"),
                    "lecture_num": result.get("lecture_num"),
                    "lecture_topic": result.get("title"),
                    "task_id": result.get("task_id"),
                    "status": result.get("status"),
                    "verified": result.get("verified"),
                },
                source=self.name,
            )
        except Exception as e:
            print(f"[NextRoundCoordinator] 后台生成下一轮资源失败: {e}")

    # ================================================================
    # 公开入口(按需)
    # ================================================================
    async def generate_next_round(self, user_id: int, topic: Optional[str] = None,
                                  mode: str = "study") -> Dict[str, Any]:
        """按需生成下一轮资源:topic 优先,否则用领域技能画像最低分技能反查。"""
        profile = get_profile(user_id)

        kp = None
        if topic:
            kps = self.rag.search_knowledge_points(topic, top_k=1)
            kp = kps[0] if kps else None
        if kp is None:
            domain_cn = self._weakest_domain(profile.domain_skills)
            kp = self._find_kp_for_domain(domain_cn) if domain_cn else None

        lecture_num = self._resolve_lecture(kp or {})
        query = topic or (kp.get("title") if kp else "")
        return await self._run_generation(user_id, lecture_num, query, mode)

    # ================================================================
    # 内部方法
    # ================================================================
    async def _run_generation(self, user_id: int, lecture_num: int,
                              query: str, mode: str) -> Dict[str, Any]:
        # 惰性导入,避免 agents → routers 的 import 顺序问题
        from ..routers.lecture import get_course_name, get_lecture_topic
        from .verification_orchestrator import get_verification_orchestrator

        course_id = settings.default_course_id
        course_title = get_course_name(course_id)
        lecture_topic = get_lecture_topic(course_id, lecture_num)
        profile = self._build_profile(user_id)

        orchestrator = get_verification_orchestrator()
        result = await orchestrator.run(
            course_id=course_id, lecture_num=lecture_num,
            course_title=course_title, lecture_topic=lecture_topic,
            profile=profile, mode=mode,
        )
        # 补充定位信息,方便前端/事件消费
        result["course_id"] = course_id
        result["lecture_num"] = lecture_num
        result["lecture_topic"] = lecture_topic

        self._cache_result(course_id, lecture_num, result)
        self._mark_generated(user_id, lecture_num)
        return result

    def _resolve_lecture(self, kp: dict) -> int:
        """薄弱知识点 → 下一讲次:source_lessons 与课程有效讲次求交取第一个。"""
        from ..routers.lecture import get_course_metadata

        source_lessons = kp.get("source_lessons") or []
        course = get_course_metadata(settings.default_course_id)
        valid = set()
        if course:
            for mod in course.get("modules", []):
                for lec in mod.get("lectures", []):
                    valid.add(lec.get("num"))
        for num in source_lessons:
            if not valid or num in valid:
                return num
        if source_lessons:
            return source_lessons[0]
        return 1

    def _build_profile(self, user_id: int) -> dict:
        p = get_profile(user_id)
        return {
            "theoretical_basis": p.theoretical_basis,
            "coding_ability": p.coding_ability,
            "practical_ops": p.practical_ops,
            "troubleshooting": p.troubleshooting,
            "data_thinking": p.data_thinking,
            "self_learning": p.self_learning,
            "domain_skills": p.domain_skills or {},
            "user_id": user_id,
            "username": p.major_background or "anonymous",
        }

    def _weakest_domain(self, domain_skills: dict) -> Optional[str]:
        if not domain_skills:
            return None
        weak_key = min(domain_skills, key=lambda k: domain_skills.get(k, 100))
        return DOMAIN_SKILL_LABELS.get(weak_key, weak_key)

    def _find_kp_for_domain(self, domain_cn: str) -> Optional[dict]:
        pts = [kp for kp in self._knowledge_points if kp.get("skill_domain") == domain_cn]
        pts.sort(key=lambda kp: kp.get("difficulty", 1))
        return pts[0] if pts else None

    def _load_knowledge_points(self) -> list:
        kp_path = os.path.join(str(settings.kb_path), "knowledge_points.json")
        try:
            with open(kp_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[NextRoundCoordinator] 加载知识点失败: {e}")
            return []

    def _recently_generated(self, user_id: int, lecture_num: int) -> bool:
        last = self._cooldown.get((user_id, lecture_num))
        if last is None:
            return False
        return time.time() - last < settings.learning_loop_cooldown_seconds

    def _mark_generated(self, user_id: int, lecture_num: int):
        self._cooldown[(user_id, lecture_num)] = time.time()

    def _cache_result(self, course_id: str, lecture_num: int, result: dict):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
            cache_file = os.path.join(CACHE_DIR, f"{course_id}_{lecture_num}.json")
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[NextRoundCoordinator] 缓存下一轮资源失败: {e}")


_next_round_coordinator = None


def get_next_round_coordinator() -> NextRoundCoordinator:
    global _next_round_coordinator
    if _next_round_coordinator is None:
        _next_round_coordinator = NextRoundCoordinator()
    return _next_round_coordinator
