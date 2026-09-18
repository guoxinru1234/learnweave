"""Agent type definitions — TypedDict input/output contracts for all 10 agent roles.
Each agent has a clearly defined responsibility, input, and output format.
"""
from typing import TypedDict, List, Dict, Any, Optional, NotRequired


# ============================================================
# 1. LearnerProfileAgent — 学情诊断
# ============================================================
class LearnerProfileInput(TypedDict, total=False):
    """诊断输入 — 所有字段可选，缺字段时使用安全默认值"""
    user_id: int
    theoretical_basis: int          # 理论基础分 0-100
    coding_ability: int             # 编程能力分 0-100
    education_background: str       # 学历背景 (高中/本科/硕士/博士)
    prior_courses: List[str]        # 已修课程列表
    learning_goal: str              # 学习目标 (就业/考研/兴趣/竞赛/转行)
    test_results: List[Dict[str, Any]]  # 测试结果 [{topic, score, total, questions}]
    historical_interactions: List[Dict[str, Any]]  # 历史交互记录
    cognitive_style: str            # 认知风格
    learning_pace: str              # 学习节奏
    answer: str                     # 对话模式: 学生本轮回答


class KnowledgeGap(TypedDict):
    knowledge_point: str   # 知识点名称
    mastery: int           # 掌握度 0-100
    evidence: str          # 诊断依据 (来自test_results或画像评分)


class LearnerProfileOutput(TypedDict):
    """结构化诊断输出 — 供 Orchestrator 直接使用"""
    learner_level: str                      # beginner | intermediate | advanced
    knowledge_gaps: List[KnowledgeGap]       # 薄弱知识点
    mastered_points: List[str]              # 已掌握知识点
    mastery_scores: Dict[str, int]          # 各维度掌握分
    recommended_difficulty: str             # basic | intermediate | advanced
    learning_strategy: str                  # 补弱/强化/均衡
    resource_requirements: List[str]        # 所需资源类型
    diagnosis_evidence: Dict[str, Any]      # 诊断依据汇总
    reasoning_summary: str                  # 诊断推理简述
    overall_score: int                      # 综合评分
    completed: bool                         # 诊断是否完成


# ============================================================
# 2. KnowledgeRetrievalAgent — 知识库检索与证据整理
# ============================================================
class KnowledgeRetrievalInput(TypedDict):
    topic: str
    top_k: NotRequired[int]  # 默认 5


class Evidence(TypedDict):
    """结构化知识证据 — 供生成 Agent 和审核 Agent 共同使用"""
    source_id: str              # 来源唯一标识
    source_title: str           # 来源标题
    source_type: str            # lecture | case | exercise | manual | dataset
    chunk_id: str               # 文本块ID
    content: str                # 证据内容（摘要/snippet）
    knowledge_points: List[str] # 关联知识点
    locator: str                # 定位器（讲次号/章节引用）
    relevance_score: float      # 相关性评分 0-1
    source_url: str             # URL（无则为空字符串）
    source_path: str            # 文件路径
    authority_level: int        # 权威等级 1-5


class KnowledgeRetrievalOutput(TypedDict):
    sources: List[Evidence]     # 证据列表（无结果时为 []）
    topic: str
    evidence_count: int         # 证据数量
    empty: bool                 # 是否为空（无知识库命中）


# ============================================================
# 3. OrchestratorAgent — 动态调度计划
# ============================================================
class DispatchInput(TypedDict, total=False):
    """调度输入 — 来自学情诊断和知识检索"""
    learner_diagnosis: Dict[str, Any]    # LearnerProfileOutput
    retrieved_evidence: List[Dict[str, Any]]  # Evidence[]
    learning_goal: str                   # 就业/考研/兴趣/竞赛/转行
    requested_resource_types: List[str]  # lecture/code/quiz/reading/video


class AgentDispatch(TypedDict):
    agent_name: str          # DocAgent | CodeAgent | QuizAgent | ReadingAgent | VideoAgent
    priority: int            # 1=required, 2=recommended, 3=optional
    reason: str              # 调度依据
    difficulty: str          # basic | intermediate | advanced
    evidence_required: bool  # 是否需要知识库证据


class DispatchPlan(TypedDict):
    task_id: str
    learner_level: str
    target_knowledge_points: List[str]
    selected_agents: List[AgentDispatch]
    dispatch_plan: str         # 调度计划描述
    difficulty: str
    required_resource_types: List[str]
    evidence_requirements: List[str]
    fallback_plan: str


# ============================================================
# 4. DocAgent — 个性化知识讲义
# ============================================================
class DocAgentInput(TypedDict):
    lecture_topic: str
    profile: Dict[str, Any]
    knowledge_context: Dict[str, Any]
    mode: str


class DocAgentOutput(TypedDict):
    lecture_doc: Dict[str, Any]  # {title, content}


# ============================================================
# 5. CodeAgent — 实操指南与可运行代码
# ============================================================
class CodeAgentInput(TypedDict):
    lecture_topic: str
    profile: Dict[str, Any]
    knowledge_context: Dict[str, Any]
    mode: str


class CodeAgentOutput(TypedDict):
    code_example: Dict[str, Any]  # {content, language}


# ============================================================
# 6. QuizAgent — 分阶测试题
# ============================================================
class QuizAgentInput(TypedDict):
    topic: str
    count: int
    profile: NotRequired[List[int]]
    difficulty: NotRequired[str]


class QuizQuestion(TypedDict):
    id: str
    topic: str
    type: str
    difficulty: str
    q: str
    options: NotRequired[List[str]]
    answer: NotRequired[int]
    explain: NotRequired[str]
    reference: NotRequired[str]


class QuizAgentOutput(TypedDict):
    topic: str
    questions: List[QuizQuestion]
    generated_by: str


# ============================================================
# 7. ProfessionalAuditAgent — 专业审核
# ============================================================
class AuditIssue(TypedDict):
    location: str
    problem: str
    severity: str  # critical | major | minor
    fix: str


class AuditScore(TypedDict):
    accuracy: int
    consistency: int
    completeness: int
    difficulty_match: int


class AuditAgentOutput(TypedDict):
    audit_report: Dict[str, Any]
    audit_passed: bool


# ============================================================
# 8. FixAgent — 根据审核问题修订
# ============================================================
class FixAgentInput(TypedDict):
    content: str  # 原始内容
    issues: List[AuditIssue]  # 审核发现的问题


class FixAgentOutput(TypedDict):
    fixed_content: str
    success: bool


# ============================================================
# 9. FeedbackAgent — 答题反馈后更新掌握度
# ============================================================
class FeedbackEvent(TypedDict):
    learner_id: int
    event_type: str  # quiz_submitted | lab_completed
    topic: NotRequired[str]
    score: NotRequired[int]
    total: NotRequired[int]


class FeedbackAgentOutput(TypedDict):
    mastery: int
    weak_points: List[Dict[str, Any]]
    recommendations: List[str]


# ============================================================
# 10. DecisionAgent — 降维/保持/进阶决策
# ============================================================
class DecisionAgentInput(TypedDict):
    profile: Dict[str, Any]  # 6维画像
    quiz_result: NotRequired[Dict[str, Any]]  # 最近答题结果
    current_difficulty: NotRequired[str]


class DecisionAction(TypedDict):
    action: str  # simplify | maintain | challenge
    reason: str
    target_topics: List[str]


class DecisionAgentOutput(TypedDict):
    actions: List[DecisionAction]
