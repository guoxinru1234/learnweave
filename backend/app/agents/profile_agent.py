"""画像智能体 — LangGraph StateGraph 驱动的自适应对话评估

StateGraph 流程:
  analyze  →  apply  →  check_complete
                              ├─ 未完成 → respond → END
                              └─ 已完成 → summarize → END
"""
import json
import re
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from ..core.llm import get_llm_client, LLMError, LLMAuthError, LLMTimeoutError
from ..core.event_bus import event_bus
from ..models.profile import (
    get_profile, save_profile, LearnerProfile,
    DOMAIN_SKILL_KEYS, DOMAIN_SKILL_LABELS,
)

# ========== 维度元数据（P3：10 领域技能维度） ==========

# 复用 profile 的领域技能维度定义（10 技能域）
DIMENSION_LABELS: dict[str, str] = DOMAIN_SKILL_LABELS
INTERVIEW_STYLE = (
    "Interview style: respond like a patient learning consultant, not a questionnaire. "
    "Acknowledge a concrete detail from the student's previous answer, then ask one "
    "contextual follow-up in 2-4 complete sentences. Ask about scenarios, steps, outcomes, "
    "obstacles, or debugging. Avoid short mechanical prompts and vary wording naturally."
)

PREFERENCE_MAP: dict[str, str] = {
    "cognitive_style": "cognitive_style",
    "learning_pace": "learning_pace",
    "learning_motivation": "learning_motivation",
}

MAX_CONVERSATION_ROUNDS = 20
MIN_DIMENSIONS_FOR_COMPLETION = 10  # 10 个领域技能维度
MIN_ROUNDS_BEFORE_COMPLETION = 8  # 至少聊8轮才能结束

SCORE_RUBRIC = """
评分必须依据学生对当前技能的明确证据，并使用以下统一锚点：
- 0-9：完全陌生，连概念或用途都不了解。
- 10-19：听说过名称或大致用途，但不会操作；明确表示从未使用通常落在本档。
- 20-39：理解部分基础概念，能说出对象、步骤或问题类型，但缺少实际操作。
- 40-59：在示例、教程或教师指导下做过简单操作，尚不能独立完成常规任务。
- 60-79：能够独立完成常规任务，并能解释主要步骤和处理一般错误。
- 80-89：完成过真实项目，能够综合使用该技能解决问题。
- 90-100：能够处理复杂场景、解释原理、优化方案或指导他人。

证据约束：
- “没听说过/完全不了解”不得高于 9 分。
- “只听说过/知道用途/从未使用/不会操作”应为 10-19 分，不得给 40 分以上。
- 只看过示例、图表或别人操作，但自己没做过，应为 10-25 分。
- 只有明确做过实际操作，才可达到 40 分；只有能独立完成，才可达到 60 分。
- 每个 assessment 的 description 必须引用该技能的具体回答证据，不能只写“基础较弱”。
- 不要为了整齐而给多个维度相同分数；相同分数必须有同等强度的证据。
"""


def _clean_visible_reply(text: str) -> str:
    """Remove provider reasoning and structured assessment payloads from UI text."""
    clean = text or ""
    clean = re.sub(r'<think\b[^>]*>[\s\S]*?</think>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<analysis\b[^>]*>[\s\S]*?</analysis>', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'```\s*\{[\s\S]*?\}\s*```', '', clean)
    clean = re.sub(r'\n?\s*\{[\s\S]*"assessments"[\s\S]*\}\s*$', '', clean)
    return clean.strip()


# ========== 系统 Prompt ==========

PROFILE_SYSTEM_PROMPT = """你是 LearnWeave 学习助手，通过友好对话了解学生的 Python 数据分析领域技能水平，构建领域技能画像。

""" + SCORE_RUBRIC + """

每轮回复末尾附加 JSON（学生看不到）：
```json
{"assessments":{"dimension_key":{"score":60,"description":"简短"}},"preferences":{},"background":"专业","next_dimension":"pandas","conversation_phase":"1/10"}
```

评分规则（非常重要）：
- 只对你已经通过对话获得足够信息的技能打分，不要猜测或预判
- 如果当前轮次没有获取到某个技能的新信息，不要给该技能打分
- 有具体项目/代码经验 → 80-95分，会基本使用 → 60-80分，只是听说过 → 40-60分
- assessments 可以为空 {}，表示本轮没有足够信息评估任何技能
- 至少需要1-2轮对话收集信息后，才能对同一个技能给出有信心的分数

十大领域技能维度（Python 数据分析方向）:
- python_basic Python基础（变量、数据类型、流程控制、函数）
- numpy NumPy（ndarray、索引切片、广播、向量化）
- pandas Pandas（Series/DataFrame、groupby、merge、数据筛选）
- data_cleaning 数据清洗（缺失值、重复值、异常值处理）
- visualization 数据可视化（Matplotlib、Seaborn）
- etl ETL管道（数据抽取、转换、加载）
- sql SQL（查询、窗口函数、数据库操作）
- statistics 统计分析（描述统计、概率分布、假设检验）
- comprehensive_analysis 综合分析（完整数据分析项目实战）
- performance 性能优化（向量化、内存优化、并行处理）

偏好: cognitive_style(动手/视觉/阅读/听觉), learning_pace(快速/稳步/慢速), learning_motivation(就业/考研/兴趣/竞赛)

对话规则:
- 自然友好，一次只问一个问题，2-3句话
- 首轮只问专业和年级，了解背景
- 逐步深入探索10个技能维度，每轮只关注1个技能
- 绝对不要在全部10维评分完成前说"总结一下"、"给你总结"、"好了"、"最后"等总结性话语
- 如果还有技能未评分（conversation_phase 不足 10/10），继续提问探索那些技能
- 只有全部10维都已评分且你有充分信心时，才设置 next_dimension="complete"
- conversation_phase 追踪已评估技能数，如 "2/10" 表示已评2个
- 进度示例：评完 Python 和 NumPy → phase=2/10，继续问 Pandas；评完5个 → phase=5/10，继续问剩下5个"""


# ========== LangGraph State ==========

class ProfileState(TypedDict, total=False):
    """LangGraph 画像对话状态

    StateGraph 每轮运行一个完整流程：
    学生回答 → LLM 分析 → 写入画像 → 检查完成 → 生成回复
    """
    user_id: int
    student_answer: str          # 本轮学生的输入
    messages: List[dict]          # 完整的 LLM 对话上下文
    assistant_reply: str          # LLM 生成的回复文本
    parsed_json: Optional[dict]   # LLM 回复中提取的 JSON 评估
    updates: List[dict]           # 本轮分数变更列表
    dialogue_step: int            # 当前对话轮数
    completed: bool               # 评估是否完成


# ========== Agent 实现 ==========

class ProfileAgent:
    """LangGraph StateGraph 驱动的学情画像评估助手

    ┌──────────┐     ┌──────────┐     ┌─────────────────┐
    │ analyze  │ ──▶ │  apply   │ ──▶ │ check_complete  │
    │ LLM分析  │     │ 写入画像  │     │ 判断是否结束     │
    └──────────┘     └──────────┘     └───────┬─────────┘
                                     ┌─────────┴─────────┐
                                     ▼                   ▼
                              ┌──────────┐        ┌──────────┐
                              │ respond  │        │summarize │
                              │ 下一问   │        │ 总结     │
                              └────┬─────┘        └────┬─────┘
                                   └─────── END ◄──────┘
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.graph = self._build_graph()

    # ===== 构建 LangGraph =====

    def _build_graph(self) -> StateGraph:
        """构建画像评估的 LangGraph StateGraph"""
        workflow = StateGraph(ProfileState)

        # 添加节点
        workflow.add_node("analyze", self._node_analyze)
        workflow.add_node("apply", self._node_apply)
        workflow.add_node("check_complete", self._node_check_complete)
        workflow.add_node("respond", self._node_respond)
        workflow.add_node("summarize", self._node_summarize)

        # 入口
        workflow.set_entry_point("analyze")

        # 主流程：分析 → 写入 → 检查完成状态
        workflow.add_edge("analyze", "apply")
        workflow.add_edge("apply", "check_complete")

        # 条件分支：完成 / 未完成
        workflow.add_conditional_edges(
            "check_complete",
            lambda state: "summarize" if state.get("completed") else "respond",
            {
                "respond": "respond",
                "summarize": "summarize",
            }
        )

        # 两种结束路径
        workflow.add_edge("respond", END)
        workflow.add_edge("summarize", END)

        return workflow.compile()

    # ===== 节点实现 =====

    async def _node_analyze(self, state: ProfileState) -> ProfileState:
        """节点 1：调用 LLM 分析学生回答，提取结构化 JSON"""
        profile = get_profile(state["user_id"])
        messages = self._build_messages(profile)
        student_answer = state.get("student_answer", "")

        if not student_answer:
            state["assistant_reply"] = "抱歉，我没有收到你的回答，能再说一遍吗？[:)]"
            state["parsed_json"] = None
            state["messages"] = messages
            state["dialogue_step"] = profile.dialogue_step
            return state

        messages.append({"role": "user", "content": student_answer})

        try:
            reply, parsed = await self._generate_reply(messages)
        except LLMAuthError:
            reply = "[WARN]️ LLM 服务未配置，请在 .env 中设置 API Key。"
            parsed = None
        except LLMTimeoutError:
            reply = "⏱️ 响应超时，请稍后再试。"
            parsed = None
        except LLMError as e:
            reply = "抱歉，我暂时遇到了一些问题 😅 让我们换个话题继续——你之前学过哪些计算机相关的课程呢？"
            parsed = None
            print(f"[ProfileAgent] LLM 错误: {e}")

        # 剥离 JSON，保存纯文本回复
        clean_reply = _clean_visible_reply(reply)

        if not clean_reply:
            clean_reply = reply.split('```')[0].strip()[:200]
        if not clean_reply:
            clean_reply = "好的，我了解了！"

        state["assistant_reply"] = clean_reply
        state["parsed_json"] = parsed
        state["messages"] = messages  # 原始 LLM 上下文（含 JSON），用于后续调试
        state["dialogue_step"] = profile.dialogue_step
        return state

    async def _node_apply(self, state: ProfileState) -> ProfileState:
        """节点 2：将 LLM 评估结果写入 LearnerProfile"""
        profile = get_profile(state["user_id"])
        updates: list[dict] = []
        parsed = state.get("parsed_json")

        if parsed is not None:
            updates = self._apply_assessments(
                profile, parsed, state.get("student_answer", "")
            )
        # 每轮对话都计数（无论 LLM 是否返回 JSON），确保最少对话轮数限制生效
        profile.dialogue_step += 1

        # 对话历史：追加用户回答和助理回复（纯文本，不含 JSON）
        student_answer = state.get("student_answer", "")
        if student_answer:
            profile.dialogue_history.append({"role": "user", "content": student_answer})
        profile.dialogue_history.append({
            "role": "assistant",
            "content": state.get("assistant_reply", "")
        })

        # 判断是否完成
        completed = self._check_completion(profile, parsed) if parsed else False
        if completed:
            profile.dialogue_completed = True

        save_profile(profile)

        state["updates"] = updates
        state["completed"] = completed
        state["dialogue_step"] = profile.dialogue_step
        return state

    async def _node_check_complete(self, state: ProfileState) -> ProfileState:
        """节点 3：纯逻辑判断节点 — 已完成 / 继续下一轮

        这个节点不做任何修改，只是透传状态。
        条件边由 check_complete → respond/summarize 的路由完成。
        """
        # 已完成的画像触发事件总线通知
        if state.get("completed"):
            profile = get_profile(state["user_id"])
            try:
                await event_bus.publish(
                    "PROFILE_COMPLETED",
                    {"user_id": state["user_id"], "profile": self._profile_dict(profile)},
                    source="画像智能体"
                )
            except Exception:
                pass

        return state

    async def _node_respond(self, state: ProfileState) -> ProfileState:
        """节点 4a：未完成 — LLM 自然回复已包含下一问，直接使用"""
        return state

    async def _node_summarize(self, state: ProfileState) -> ProfileState:
        """节点 4b：已完成 — 生成最终总结"""
        profile = get_profile(state["user_id"])
        reply = _clean_visible_reply(state.get("assistant_reply", ""))

        # 如果 LLM 没有给出完整的总结，补生成一段
        if not reply or len(reply) < 10:
            reply = await self._generate_final_summary(profile)

        # 更新对话历史中的最后一条回复
        if profile.dialogue_history and \
           profile.dialogue_history[-1].get("role") == "assistant":
            profile.dialogue_history[-1]["content"] = reply

        state["assistant_reply"] = reply
        save_profile(profile)
        return state

    # ===== 公开 API（与旧接口完全兼容） =====

    async def start_conversation(self, user_id: int) -> Dict[str, Any]:
        """LLM 生成开场白（不使用 StateGraph，单次 LLM 调用即可）"""
        profile = get_profile(user_id)

        messages = [
            {"role": "system", "content": PROFILE_SYSTEM_PROMPT},
            {"role": "user", "content": "请开始画像评估对话。先简单自我介绍（你是 LearnWeave 学习助手），然后友好问候学生。第一轮只问专业和年级，不要提具体技术栈或编程语言。"},
        ]

        try:
            reply, _ = await self._generate_reply(messages)
        except LLMError:
            reply = "你好！我是 LearnWeave 的学习助手 🤗 很高兴认识你！先简单了解一下——你的专业和年级是什么？想学哪方面的内容？"

        profile.dialogue_history.append({"role": "assistant", "content": _clean_visible_reply(reply)})
        profile.dialogue_step = 0
        save_profile(profile)

        return self._make_response(profile, [], 0, False)

    async def process_answer(self, user_id: int, answer: str) -> Dict[str, Any]:
        """处理学生的一轮回答，LangGraph StateGraph 驱动完整流程

        StateGraph 路径:
          analyze → apply → check_complete → respond (或 summarize) → END
        """
        initial_state: ProfileState = {
            "user_id": user_id,
            "student_answer": answer,
            "messages": [],
            "assistant_reply": "",
            "parsed_json": None,
            "updates": [],
            "dialogue_step": 0,
            "completed": False,
        }

        result = await self.graph.ainvoke(initial_state)

        profile = get_profile(user_id)
        return self._make_response(
            profile,
            result.get("updates", []),
            result.get("dialogue_step", 0),
            result.get("completed", False),
        )

    # ===== 内部方法（与旧实现兼容） =====

    def _build_messages(self, profile: LearnerProfile) -> list[dict]:
        """构建完整消息列表：系统 Prompt + 对话历史 + 进度上下文"""
        messages = [{"role": "system", "content": PROFILE_SYSTEM_PROMPT + "\n\n" + INTERVIEW_STYLE}]

        for msg in profile.dialogue_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        progress = self._build_progress_context(profile)
        messages.append({"role": "system", "content": progress})

        return messages

    def _build_progress_context(self, profile: LearnerProfile) -> str:
        """构建评估进度上下文"""
        assessed = []
        unassessed = []
        for key, label in DIMENSION_LABELS.items():
            score = profile.domain_skills.get(key, 0)
            if score > 0:
                assessed.append(f"  [OK] {label}({key}): {score}/100")
            else:
                unassessed.append(f"  ⬜ {label}({key}): 待评估")

        lines = ["## 当前评估进度"]
        lines.append(f"已评估: {len(assessed)}/10 个技能")
        lines.extend(assessed)
        if unassessed:
            lines.append("待评估:")
            lines.extend(unassessed)

        prefs = []
        if profile.cognitive_style:
            prefs.append(f"认知风格={profile.cognitive_style}")
        if profile.learning_pace:
            prefs.append(f"学习节奏={profile.learning_pace}")
        if profile.learning_motivation:
            prefs.append(f"学习动机={profile.learning_motivation}")
        if prefs:
            lines.append(f"偏好: {', '.join(prefs)}")
        if profile.major_background:
            lines.append(f"背景: {profile.major_background}")

        lines.append(f"\n对话轮数: {profile.dialogue_step}")
        lines.append("\n请继续自然对话。优先探索「待评估」的维度。如果所有维度都已评估，请将 next_dimension 设为 'complete' 并自然结束对话。")

        return "\n".join(lines)

    async def _generate_reply(self, messages: list[dict]) -> tuple[str, Optional[dict]]:
        """调用 LLM，返回 (纯文本回复, 解析后的JSON或None)。
        如果首次调用未返回 JSON，则追加提示重试一次。"""
        response = await self.llm.chat(messages, temperature=0.7, max_tokens=2048)
        parsed = self._extract_json(response)

        # 如果 LLM 忘记输出 JSON，追加明确提示重试一次
        if parsed is None:
            retry_messages = messages + [
                {"role": "assistant", "content": response},
                {"role": "system",
                 "content": "你忘记在回复末尾附加 JSON 评估数据了。请根据上一轮对话只输出 JSON（不要重复对话内容）：\n"
                            "{\"assessments\": {\"dimension_key\": {\"score\": 0-100, \"description\": \"评语\"}}, "
                            "\"preferences\": {}, \"background\": \"...\", "
                            "\"next_dimension\": \"...\", \"conversation_phase\": \"X/10\"}"},
            ]
            try:
                retry_response = await self.llm.chat(retry_messages, temperature=0.3, max_tokens=1024)
                retry_parsed = self._extract_json(retry_response)
                if retry_parsed:
                    parsed = retry_parsed
            except Exception:
                pass  # 重试失败不影响主流程

        # 剥离 JSON 代码块，只保留用户可见文本
        clean_reply = _clean_visible_reply(response)

        if not clean_reply:
            clean_reply = response.split('```')[0].strip()[:200]
        if not clean_reply:
            clean_reply = "好的，我了解了！"

        return clean_reply, parsed

    def _extract_json(self, text: str) -> Optional[dict]:
        """从 LLM 回复中提取结构化 JSON"""
        # 1. 尝试 fenced code block
        m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        # 2. 尝试匹配包含关键字段的裸 JSON
        for key in ["assessments", "next_dimension", "conversation_phase"]:
            m = re.search(r'\{[\s\S]*"' + key + r'"[\s\S]*\}', text)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    continue

        # 3. 兜底：从后往前找最后一个 JSON 对象
        brace_positions = [i for i, c in enumerate(text) if c == '{']
        for start in reversed(brace_positions):
            depth = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            if end > start:
                candidate = text[start:end]
                try:
                    result = json.loads(candidate)
                    if isinstance(result, dict) and any(
                        k in result for k in ("assessments", "next_dimension", "conversation_phase")
                    ):
                        return result
                except json.JSONDecodeError:
                    continue

        return None

    @staticmethod
    def _evidence_score_cap(answer: str) -> Optional[int]:
        """Cap self-reported scores when the answer explicitly denies experience."""
        normalized = re.sub(r"\s+", "", (answer or "").lower())
        if not normalized:
            return None

        no_awareness = ("没听说过", "完全不了解", "不知道是什么")
        no_practice = (
            "没有接触过", "没有使用过", "没使用过", "从未使用", "没有学过",
            "没学过", "不会操作", "没有实际", "没做过", "没有做过",
            "没有正式写过", "没有独立", "还不会", "不太了解",
        )
        observed_only = ("只是听说过", "只听说过", "看过", "知道用途")

        if any(term in normalized for term in no_awareness):
            return 9
        if any(term in normalized for term in no_practice):
            return 19
        if any(term in normalized for term in observed_only):
            return 25
        return None

    def _apply_assessments(
        self, profile: LearnerProfile, analysis: dict, student_answer: str = ""
    ) -> list[dict]:
        """将 LLM 评估结果写入画像，返回变更列表"""
        updates: list[dict] = []

        assessments = analysis.get("assessments", {})
        if isinstance(assessments, dict):
            for dim_key, dim_data in assessments.items():
                if dim_key not in DIMENSION_LABELS:
                    continue

                score = dim_data.get("score", 0) if isinstance(dim_data, dict) else dim_data
                try:
                    score = max(0, min(100, int(score)))
                except (ValueError, TypeError):
                    continue

                evidence_cap = self._evidence_score_cap(student_answer)
                if evidence_cap is not None:
                    score = min(score, evidence_cap)

                if score <= 0:
                    continue

                old = profile.domain_skills.get(dim_key, 0)
                if score > 0 and score != old:
                    profile.domain_skills[dim_key] = score

                    updates.append({
                        "dimension": dim_key,
                        "old": old,
                        "new": score,
                        "change": score - old,
                    })

        prefs = analysis.get("preferences", {})
        if isinstance(prefs, dict):
            for json_key, profile_attr in PREFERENCE_MAP.items():
                value = prefs.get(json_key, "").strip() if prefs.get(json_key) else ""
                if value and not getattr(profile, profile_attr, ""):
                    setattr(profile, profile_attr, value)

        if not profile.major_background:
            bg = analysis.get("background", "")
            if bg and isinstance(bg, str) and len(bg) > 1:
                profile.major_background = bg

        return updates

    def _check_completion(self, profile: LearnerProfile, analysis: dict) -> bool:
        """判断对话是否完成。

        必须同时满足三个条件：
        1. LLM 主动标记 complete（next_dimension == "complete"）
        2. 全部 6 个维度都有评分
        3. 至少完成 MIN_ROUNDS_BEFORE_COMPLETION 轮对话
        （达到 MAX_CONVERSATION_ROUNDS 上限也强制结束）
        """
        if profile.dialogue_step >= MAX_CONVERSATION_ROUNDS:
            return True

        if analysis.get("next_dimension") == "complete":
            scored = sum(1 for d in DIMENSION_LABELS if profile.domain_skills.get(d, 0) > 0)
            enough_rounds = profile.dialogue_step >= MIN_ROUNDS_BEFORE_COMPLETION
            return scored >= MIN_DIMENSIONS_FOR_COMPLETION and enough_rounds

        return False

    async def _generate_final_summary(self, profile: LearnerProfile) -> str:
        """对话完成时生成总结"""
        weak = profile.domain_weak_skills
        strong = profile.domain_strong_skills

        if not weak or not strong:
            return "评估完成！你的领域技能画像已建立，可以在学情画像页查看雷达图。接下来从你最薄弱的数据分析技能开始学习吧！"

        prompt = f"""你是学情画像助手。评估已完成，请做简短总结。

学生的强项：{strong[0][0]}({strong[0][1]}分)、{strong[1][0] if len(strong) > 1 else '—'}({strong[1][1] if len(strong) > 1 else 0}分)
薄弱方向：{weak[0][0]}({weak[0][1]}分)、{weak[1][0] if len(weak) > 1 else '—'}({weak[1][1] if len(weak) > 1 else 0}分)

请生成 3-4 句鼓励性的总结，点出 1-2 个强项和 1 个需要加强的数据分析技能，然后提出下一步建议。"""

        try:
            return await self.llm.chat([
                {"role": "system", "content": "你是友好的学习助手，擅长给学生积极的反馈和实用的建议。用中文，3-4句话。"},
                {"role": "user", "content": prompt},
            ], temperature=0.7, max_tokens=300)
        except LLMError:
            return f"[Party] 评估完成！你的强项是{strong[0][0]}（{strong[0][1]}分），可以继续发挥优势；建议重点加强{weak[0][0]}方向。点击下方按钮开始学习之旅吧！"

    # ===== 辅助方法 =====

    def _profile_dict(self, profile: LearnerProfile) -> dict:
        return {
            "major_background": profile.major_background,
            "domain_skills": profile.domain_skills,
            "domain_weak_skills": profile.domain_weak_skills,
            "domain_strong_skills": profile.domain_strong_skills,
            "theoretical_basis": profile.theoretical_basis,
            "coding_ability": profile.coding_ability,
            "practical_ops": profile.practical_ops,
            "troubleshooting": profile.troubleshooting,
            "data_thinking": profile.data_thinking,
            "self_learning": profile.self_learning,
            "overall_score": profile.overall_score,
            "weak_dimensions": profile.weak_dimensions,
            "strong_dimensions": profile.strong_dimensions,
            "cognitive_style": profile.cognitive_style,
            "learning_pace": profile.learning_pace,
            "learning_motivation": profile.learning_motivation,
        }

    def _make_response(self, profile: LearnerProfile, updates: list[dict],
                       step: int, completed: bool) -> dict:
        return {
            "message": profile.dialogue_history[-1]["content"] if profile.dialogue_history else "",
            "profile": self._profile_dict(profile),
            "updates": updates,
            "dialogue_step": step,
            "completed": completed,
            "completion_percentage": profile.completion_percentage,
            "descriptions": {
                "theory_description": profile.theory_description,
                "coding_description": profile.coding_description,
                "practice_description": profile.practice_description,
                "debug_description": profile.debug_description,
                "data_description": profile.data_description,
                "self_learning_description": profile.self_learning_description,
            },
        }


    # ===== 结构化诊断（新增） =====

    def diagnose(self, input_data: dict) -> dict:
        """根据多维输入生成结构化诊断结果。

        支持字段: theoretical_basis, coding_ability, education_background,
                  prior_courses, learning_goal, test_results, historical_interactions,
                  cognitive_style, learning_pace.

        缺失字段使用安全默认值，不抛异常。
        返回结构化的 LearnerProfileOutput，可直接供 Orchestrator 使用。
        """
        profile = input_data.get("user_id") and get_profile(input_data["user_id"])
        dims = {
            "theoretical_basis": input_data.get("theoretical_basis") or (profile.theoretical_basis if profile else 0) or 0,
            "coding_ability": input_data.get("coding_ability") or (profile.coding_ability if profile else 0) or 0,
            "practical_ops": (profile.practical_ops if profile else 0) or 0,
            "troubleshooting": (profile.troubleshooting if profile else 0) or 0,
            "data_thinking": (profile.data_thinking if profile else 0) or 0,
            "self_learning": (profile.self_learning if profile else 0) or 0,
        }
        test_results = input_data.get("test_results") or []
        prior_courses = input_data.get("prior_courses") or []
        education_bg = input_data.get("education_background") or (profile.major_background if profile else "") or ""
        learning_goal = input_data.get("learning_goal") or (profile.learning_motivation if profile else "") or ""

        # 计算综合评分
        valid_scores = [v for v in dims.values() if v > 0]
        overall = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 30

        # 判定学习者水平
        if overall < 35:
            level = "beginner"
        elif overall < 70:
            level = "intermediate"
        else:
            level = "advanced"

        # 知识点掌握（从画像 + 测试结果推导）
        dim_labels = {
            "theoretical_basis": "理论基础", "coding_ability": "编程能力",
            "practical_ops": "实践操作", "troubleshooting": "问题排查",
            "data_thinking": "数据思维", "self_learning": "自学能力",
        }
        knowledge_gaps = []
        mastered_points = []
        for key, score in dims.items():
            label = dim_labels.get(key, key)
            evidence = f"画像评分: {score}/100"
            # 如果有测试结果，引用（topic包含维度标签 或 维度标签包含topic关键词）
            for tr in test_results:
                if isinstance(tr, dict):
                    t = tr.get("topic", "").lower()
                    if label.lower() in t or any(kw in t for kw in label.lower().split()):
                        evidence += f"；测试得分: {tr.get('score', '?')}/{tr.get('total', '?')}"
                        break
            if score < 50:
                knowledge_gaps.append({"knowledge_point": label, "mastery": score, "evidence": evidence})
            elif score >= 70:
                mastered_points.append(label)

        # 推荐难度
        if overall < 40:
            recommended_difficulty = "basic"
        elif overall < 70:
            recommended_difficulty = "intermediate"
        else:
            recommended_difficulty = "advanced"

        # 学习策略
        if len(knowledge_gaps) >= 3:
            learning_strategy = "补弱优先：重点攻克薄弱维度"
        elif len(mastered_points) >= 4:
            learning_strategy = "强化优势：在已掌握领域深入拓展"
        else:
            learning_strategy = "均衡发展：各维度同步推进"

        # 资源需求
        resource_requirements = []
        if dims["theoretical_basis"] < 50 or dims["coding_ability"] < 50:
            resource_requirements.append("基础讲义 + 代码示例")
        if dims["practical_ops"] < 50 or dims["troubleshooting"] < 50:
            resource_requirements.append("实操实验室 + 排错练习")
        if dims["data_thinking"] < 50:
            resource_requirements.append("数据分析案例集")
        if overall >= 60:
            resource_requirements.append("进阶拓展阅读")
        if overall >= 80:
            resource_requirements.append("工业级实战项目")

        # 诊断证据
        diagnosis_evidence = {
            "source": "profile_agent.diagnose()",
            "input_fields_provided": [k for k in input_data if input_data.get(k)],
            "dimensions_assessed": len(valid_scores),
            "test_results_count": len(test_results),
            "has_historical_data": bool(input_data.get("historical_interactions")),
        }

        return {
            "learner_level": level,
            "knowledge_gaps": knowledge_gaps,
            "mastered_points": mastered_points,
            "mastery_scores": dims,
            "recommended_difficulty": recommended_difficulty,
            "learning_strategy": learning_strategy,
            "resource_requirements": resource_requirements,
            "diagnosis_evidence": diagnosis_evidence,
            "reasoning_summary": (
                f"基于{len(valid_scores)}维度评分（均分{overall}）、"
                f"{len(test_results)}次测试记录、"
                f"{education_bg or '未知'}学历背景、"
                f"学习目标{learning_goal or '未指定'}，"
                f"判定为{level}水平，推荐{difficulty_map[recommended_difficulty]}难度资源，"
                f"采{learning_strategy}策略。"
            ),
            "overall_score": overall,
            "completed": len(valid_scores) >= 2,
        }

    # ===== 辅助方法 =====


difficulty_map = {"basic": "基础", "intermediate": "中级", "advanced": "高级"}


# ===== 工厂函数 =====

def get_profile_agent() -> ProfileAgent:
    return ProfileAgent()
