"""LangGraph 多Agent 编排器 — 画像→路径→资源→评估 闭环"""
import asyncio
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from .path_planner import PathPlannerAgent
from .resource_agent import ResourceAgent
from .quiz_agent import QuizAgent
from .tutor_agent import TutorAgent
from .assessment_agent import AssessmentAgent


# 实际 6 维画像名称（与 profile_agent / profile model 一致）
DIM_NAMES = ["理论基础", "编程能力", "实践操作", "问题排查", "数据思维", "自学能力"]


class AgentState(TypedDict):
    messages: List[dict]
    profile: List[int]       # 6维画像
    learning_path: dict      # 学习路径
    resources: dict          # 资源生成结果
    tutoring: dict           # 辅导答疑结果
    quiz: dict               # 出题结果
    assessment: dict         # 评估结果
    focus_topic: str         # 当前重点主题
    current_phase: str
    done: bool


class LearnWeaveOrchestrator:
    """LangGraph 多 Agent 编排器"""

    def __init__(self):
        self.path_planner = PathPlannerAgent()
        self.resource_agent = ResourceAgent()
        self.quiz_agent = QuizAgent()
        self.tutor_agent = TutorAgent()
        self.assessment_agent = AssessmentAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("analyze_profile", self._analyze_profile)
        workflow.add_node("plan_path", self._plan_path)
        workflow.add_node("generate_resources", self._generate_resources)
        workflow.add_node("assess", self._assess)
        workflow.set_entry_point("analyze_profile")
        workflow.add_edge("analyze_profile", "plan_path")
        workflow.add_edge("plan_path", "generate_resources")
        workflow.add_edge("generate_resources", "assess")
        workflow.add_edge("assess", END)
        return workflow.compile()

    # ---- 节点 1：分析画像，找出最薄弱维度 ----

    def _analyze_profile(self, state: AgentState) -> AgentState:
        state["current_phase"] = "analyzing"
        profile = state["profile"]
        weak_idx = profile.index(min(profile))
        state["focus_topic"] = DIM_NAMES[weak_idx]
        return state

    # ---- 节点 2：学习路径规划 ----

    def _plan_path(self, state: AgentState) -> AgentState:
        state["learning_path"] = self.path_planner.plan(state["profile"])
        state["current_phase"] = "planning"
        return state

    # ---- 节点 3：资源 + 答疑 + 出题 并行生成 ----

    def _generate_resources(self, state: AgentState) -> AgentState:
        state["current_phase"] = "generating"
        focus = state["focus_topic"]
        profile = state["profile"]

        # 资源生成（同步）
        state["resources"] = self.resource_agent.generate(focus)

        # 答疑（async，在同步节点中用 asyncio.run）
        try:
            state["tutoring"] = asyncio.run(
                self.tutor_agent.answer(
                    f"请介绍{focus}相关的核心知识点和学习建议",
                    focus
                )
            )
        except Exception as e:
            state["tutoring"] = {"answer": f"答疑生成中: {e}", "sources": [], "follow_up": []}

        # 出题（同步）
        state["quiz"] = self.quiz_agent.generate(focus, count=3, profile=profile)

        return state

    # ---- 节点 4：综合评估 ----

    def _assess(self, state: AgentState) -> AgentState:
        state["current_phase"] = "assessing"
        state["assessment"] = self.assessment_agent.assess(
            state["profile"],
            context={"topic": state["focus_topic"], "quiz": state.get("quiz", {})}
        )
        state["done"] = True
        return state

    # ---- 入口 ----

    def run(self, profile: List[int]) -> dict:
        initial_state: AgentState = {
            "messages": [],
            "profile": profile,
            "learning_path": {},
            "resources": {},
            "tutoring": {},
            "quiz": {},
            "assessment": {},
            "focus_topic": "",
            "current_phase": "init",
            "done": False,
        }
        result = self.graph.invoke(initial_state)
        return result
