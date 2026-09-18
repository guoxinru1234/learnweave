"""统一多 Agent 编排器 —— LangGraph StateGraph。

这是比赛提交的核心架构件。7 个专业 Agent 并行生成 6+ 类个性化学习资源。

架构：
    load_context（加载知识库上下文）
        |
        +-------+-------+-------+-------+-------+-------+
        |       |       |       |       |       |       |
    DocAgent  Mindmap  CodeAgent QuizAgent Reading VideoAgent ManimAgent
        |       |       |       |       |       |       |
        +-------+-------+-------+-------+-------+-------+
        |
    plan_path（路径规划）
        |
    synthesize（汇聚响应）
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from .state import LearnWeaveState
from .doc_agent import DocAgent
from .mindmap_agent import MindmapAgent
from .code_agent import CodeAgent
from .reading_agent import ReadingAgent
from .video_agent import VideoAgent
from .manim_agent import ManimAgent
from ..rag.engine import RAGEngine
from ..core.config import settings
from ..core.llm import get_llm_client
from ..core.event_bus import event_bus


class UnifiedOrchestrator:
    """LangGraph 多 Agent 编排器 — 7 个专业 Agent 并行协作。

    每个节点只返回自己修改的字段（LangGraph TypedDict reducer 模式），
    避免并行分支的并发写入冲突。
    """

    def __init__(self):
        self.rag = RAGEngine(str(settings.kb_path))
        self.llm = get_llm_client()

        self.doc_agent = DocAgent()
        self.mindmap_agent = MindmapAgent()
        self.code_agent = CodeAgent()
        self.reading_agent = ReadingAgent()
        self.video_agent = VideoAgent()
        self.manim_agent = ManimAgent()

        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(LearnWeaveState)

        workflow.add_node("load_context", self._node_load_context)
        workflow.add_node("generate_lecture", self._node_generate_lecture)
        workflow.add_node("generate_mindmap", self._node_generate_mindmap)
        workflow.add_node("generate_quiz", self._node_generate_quiz)
        workflow.add_node("generate_code", self._node_generate_code)
        workflow.add_node("generate_reading", self._node_generate_reading)
        workflow.add_node("generate_video", self._node_generate_video)
        workflow.add_node("generate_manim", self._node_generate_manim)
        workflow.add_node("plan_path", self._node_plan_path)
        workflow.add_node("synthesize", self._node_synthesize)

        workflow.set_entry_point("load_context")

        # 扇出: 5 个 Agent 并行
        for node in ["generate_quiz", "generate_code",
                      "generate_reading", "generate_video", "generate_manim"]:
            workflow.add_edge("load_context", node)
            workflow.add_edge(node, "plan_path")
        # DocAgent 先跑，MindmapAgent 等讲义生成后再基于内容生成导图
        workflow.add_edge("load_context", "generate_lecture")
        workflow.add_edge("generate_lecture", "generate_mindmap")
        workflow.add_edge("generate_mindmap", "plan_path")

        workflow.add_edge("plan_path", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    # ==================== 节点实现 ====================

    async def _node_load_context(self, state: LearnWeaveState) -> dict:
        topic = state.get("lecture_topic", "")
        course_id = state.get("course_id", "")
        lecture_num = state.get("lecture_num", 0)

        context = {}

        cache_file = Path("data/lecture_cache") / f"{course_id}_{lecture_num}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    context = json.load(f)
            except Exception as e:
                print(f"[Orchestrator] cache read error: {e}")

        if not context or not context.get("sources"):
            rag_results = self.rag.search(topic, top_k=5)
            context["sources"] = rag_results
            context["topic"] = topic

        return {"knowledge_context": context,
                "agent_logs": [{"agent": "load_context", "status": "done",
                                "sources": len(context.get("sources", []))}]}

    async def _node_generate_lecture(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "DocAgent", "message": "开始生成课程讲义..."})
        try:
            result = await self.doc_agent.execute(dict(state))
            doc = result.get("lecture_doc", {})
            event_bus.publish("agent_done", {"agent": "DocAgent", "status": "success"})
            return {"lecture_doc": doc,
                    "agent_logs": [{"agent": "DocAgent", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "DocAgent", "error": str(e)})
            return {"lecture_doc": {"title": state.get("lecture_topic", ""),
                                    "content": "<p>讲义生成失败</p>"},
                    "agent_logs": [{"agent": "DocAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_mindmap(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "MindmapAgent", "message": "开始生成思维导图..."})
        try:
            result = await self.mindmap_agent.execute(dict(state))
            mm = result.get("mindmap", {})
            event_bus.publish("agent_done", {"agent": "MindmapAgent", "status": "success"})
            return {"mindmap": mm,
                    "agent_logs": [{"agent": "MindmapAgent", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "MindmapAgent", "error": str(e)})
            return {"mindmap": {"nodes": []},
                    "agent_logs": [{"agent": "MindmapAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_quiz(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "QuizAgent", "message": "开始生成练习题..."})
        try:
            from .quiz_agent import get_quiz_agent
            topic = state.get("lecture_topic", "")
            profile = state.get("profile", {})
            profile_vals = list(profile.values()) if profile else None

            quiz_agent = get_quiz_agent()
            import asyncio
            result = await asyncio.to_thread(
                quiz_agent.generate, topic, count=4, profile=profile_vals
            )
            event_bus.publish("agent_done", {"agent": "QuizAgent", "status": "success"})
            return {"quiz": result,
                    "agent_logs": [{"agent": "QuizAgent", "status": "success",
                                    "generated_by": result.get("generated_by", "unknown")}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "QuizAgent", "error": str(e)})
            return {"quiz": {"questions": []},
                    "agent_logs": [{"agent": "QuizAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_code(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "CodeAgent", "message": "开始生成代码案例..."})
        try:
            result = await self.code_agent.execute(dict(state))
            code = result.get("code_example", {})
            event_bus.publish("agent_done", {"agent": "CodeAgent", "status": "success"})
            return {"code_example": code,
                    "agent_logs": [{"agent": "CodeAgent", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "CodeAgent", "error": str(e)})
            return {"code_example": {"content": "// 代码生成失败", "language": "scala"},
                    "agent_logs": [{"agent": "CodeAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_reading(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "ReadingAgent", "message": "开始生成拓展阅读..."})
        try:
            result = await self.reading_agent.execute(dict(state))
            reading = result.get("extended_reading", {})
            event_bus.publish("agent_done", {"agent": "ReadingAgent", "status": "success"})
            return {"extended_reading": reading,
                    "agent_logs": [{"agent": "ReadingAgent", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "ReadingAgent", "error": str(e)})
            return {"extended_reading": {"recommendations": []},
                    "agent_logs": [{"agent": "ReadingAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_video(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "VideoAgent", "message": "开始生成视频分镜..."})
        try:
            result = await self.video_agent.execute(dict(state))
            vs = result.get("video_script", {})
            event_bus.publish("agent_done", {"agent": "VideoAgent", "status": "success"})
            return {"video_script": vs,
                    "agent_logs": [{"agent": "VideoAgent", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "VideoAgent", "error": str(e)})
            return {"video_script": {"scenes": []},
                    "agent_logs": [{"agent": "VideoAgent", "status": "error", "error": str(e)}]}

    async def _node_generate_manim(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "ManimAgent", "message": "开始生成Manim动画..."})
        try:
            result = await self.manim_agent.execute(dict(state))
            event_bus.publish("agent_done", {"agent": "ManimAgent", "status": "success"})
            return {"manim_video": result.get("manim_video"),
                    "manim_script": result.get("manim_script"),
                    "agent_logs": [{"agent": "ManimAgent", "status": "success",
                                    "personalized_for": result.get("personalized_for", {})}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "ManimAgent", "error": str(e)})
            return {"manim_video": None, "manim_script": None,
                    "agent_logs": [{"agent": "ManimAgent", "status": "error", "error": str(e)}]}

    async def _node_plan_path(self, state: LearnWeaveState) -> dict:
        event_bus.publish("agent_start", {"agent": "PathPlanner", "message": "开始规划学习路径..."})
        try:
            from .path_planner import PathPlannerAgent
            profile = state.get("profile", {})
            profile_vals = list(profile.values()) if profile else [50] * 6
            int_vals = [v for v in profile_vals if isinstance(v, (int, float)) and v > 0]
            if not int_vals:
                int_vals = [50, 50, 50, 50, 50, 50]

            planner = PathPlannerAgent()
            result = planner.plan(int_vals)
            event_bus.publish("agent_done", {"agent": "PathPlanner", "status": "success"})
            return {"learning_path": result,
                    "agent_logs": [{"agent": "PathPlanner", "status": "success"}]}
        except Exception as e:
            event_bus.publish("agent_error", {"agent": "PathPlanner", "error": str(e)})
            return {"learning_path": {"path": []},
                    "agent_logs": [{"agent": "PathPlanner", "status": "error", "error": str(e)}]}

    async def _node_synthesize(self, state: LearnWeaveState) -> dict:
        """质量验证 — 检查每个 Agent 的产出。"""
        quality_checks = []

        doc = state.get("lecture_doc", {})
        quality_checks.append({
            "resource": "lecture_doc",
            "status": "pass" if len(doc.get("content", "")) >= 100 else "warning",
            "msg": f"讲义 {len(doc.get('content', ''))} 字符"
        })

        mm = state.get("mindmap", {})
        nc = len(mm.get("nodes", []))
        quality_checks.append({
            "resource": "mindmap",
            "status": "pass" if nc >= 3 else "warning",
            "msg": f"导图 {nc} 节点"
        })

        code = state.get("code_example", {})
        cc = len(code.get("content", ""))
        quality_checks.append({
            "resource": "code_example",
            "status": "pass" if cc >= 50 else "warning",
            "msg": f"代码 {cc} 字符"
        })

        quiz = state.get("quiz", {})
        qc = len(quiz.get("questions", []))
        quality_checks.append({
            "resource": "quiz",
            "status": "pass" if qc >= 2 else "warning",
            "msg": f"练习题 {qc} 道"
        })

        reading = state.get("extended_reading", {})
        rc = len(reading.get("recommendations", []))
        quality_checks.append({
            "resource": "extended_reading",
            "status": "pass" if rc >= 2 else "warning",
            "msg": f"推荐 {rc} 条"
        })

        video = state.get("video_script", {})
        sc = len(video.get("scenes", []))
        quality_checks.append({
            "resource": "video_script",
            "status": "pass" if sc >= 2 else "warning",
            "msg": f"分镜 {sc} 页"
        })

        manim_video = state.get("manim_video")
        manim_script = state.get("manim_script")
        if manim_video and os.path.exists(str(manim_video)):
            quality_checks.append({"resource": "manim_animation", "status": "pass", "msg": "动画已生成"})
        elif manim_script:
            quality_checks.append({"resource": "manim_animation", "status": "warning", "msg": "脚本已生成但渲染失败"})
        else:
            quality_checks.append({"resource": "manim_animation", "status": "warning", "msg": "动画未生成"})

        warnings = [c for c in quality_checks if c["status"] == "warning"]
        passed = [c for c in quality_checks if c["status"] == "pass"]

        return {
            "quality_report": {
                "total": len(quality_checks),
                "passed": len(passed),
                "warnings": len(warnings),
                "checks": quality_checks,
                "overall": "good" if len(warnings) <= 1 else "needs_review",
            },
            "done": True,
            "agent_logs": [{"agent": "QualityVerifier", "status": "success",
                            "passed": len(passed), "warnings": len(warnings)}],
        }

    # ==================== 公共 API ====================

    async def run(self, course_id: str, lecture_num: int,
                  course_title: str, lecture_topic: str,
                  profile: Dict[str, Any] = None,
                  mode: str = "study") -> Dict[str, Any]:
        """主入口：运行完整的多 Agent 资源生成流程（7 个 Agent 并行）。

        Returns:
            向后兼容的字典，包含 lecture_doc, mindmap, quiz, code_example,
            extended_reading, video_script, manim_video, learning_path, agent_logs
        """
        initial_state: LearnWeaveState = {
            "course_id": course_id,
            "lecture_num": lecture_num,
            "course_title": course_title,
            "lecture_topic": lecture_topic,
            "profile": profile or {},
            "mode": mode,
            "knowledge_context": {},
            "lecture_doc": {},
            "mindmap": {},
            "quiz": {},
            "code_example": {},
            "extended_reading": {},
            "video_script": {},
            "manim_video": None,
            "manim_script": None,
            "learning_path": {},
            "agent_logs": [],
            "messages": [],
            "errors": [],
            "done": False,
        }

        result = await self.graph.ainvoke(initial_state)
        return self._format_response(result)

    def _format_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        lecture_doc = state.get("lecture_doc", {})
        code_example = state.get("code_example", {})
        mindmap = state.get("mindmap", {})
        quiz = state.get("quiz", {})
        extended_reading = state.get("extended_reading", {})
        video_script = state.get("video_script", {})
        learning_path = state.get("learning_path", {})
        agent_logs = state.get("agent_logs", [])

        video_url = video_script.get("video_url", None)
        manim_video_path = state.get("manim_video")
        manim_url = f"/media/videos/{os.path.basename(str(manim_video_path))}" if manim_video_path else None

        first_question = {}
        if quiz.get("questions"):
            first_question = quiz["questions"][0]

        return {
            "title": lecture_doc.get("title", ""),
            "type": "理论课",
            "content": lecture_doc.get("content", ""),
            "code": code_example.get("content", "// 代码生成失败"),
            "mindmap": mindmap.get("nodes", []),
            "quiz": first_question,
            "full_quiz": quiz,
            "extended_reading": extended_reading,
            "video_script": video_script,
            "video_url": video_url,
            "manim_video": manim_url,
            "manim_script": state.get("manim_script"),
            "learning_path": learning_path,
            "quality_report": state.get("quality_report", {}),
            "agent_logs": agent_logs,
            "generated_by": "multi_agent_orchestrator",
            "agent_count": len([l for l in agent_logs if l.get("status") == "success"]),
            "total_agents": 7,
        }


# ==================== 全局单例 ====================

_unified_orchestrator: UnifiedOrchestrator | None = None


def get_unified_orchestrator() -> UnifiedOrchestrator:
    global _unified_orchestrator
    if _unified_orchestrator is None:
        _unified_orchestrator = UnifiedOrchestrator()
    return _unified_orchestrator
