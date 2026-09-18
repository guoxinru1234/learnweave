"""LearnWeave 多 Agent 系统共享状态定义。

所有 Agent 通过此状态互相通信。
LangGraph StateGraph 以 LearnWeaveState 为状态类型。

修复说明: 使用 Annotated + reducer 解决并行分支并发写入冲突。
7 个 Agent 并行执行后汇聚到 plan_path，每个 key 都需要 reducer 来合并。
"""
import operator
from typing import TypedDict, List, Dict, Any, Annotated


def _merge_logs(a: list, b: list) -> list:
    """合并 agent_logs: 去重 + 保持顺序。"""
    if not a:
        return b or []
    if not b:
        return a
    return a + b


def _keep_last(a, b):
    """Reducer: 保留后写入的值（并行分支用最后完成的）。"""
    return b if b is not None else a


class LearnWeaveState(TypedDict, total=False):
    """统一编排器的共享状态。

    每个 Agent 读取自己需要的字段，产出结果写入对应字段。
    LangGraph 的 add_edge 模式意味着所有 Agent 写入的字段
    在汇聚节点（plan_path）中可以全部访问。
    """

    # ---- 学生身份 ----
    user_id: int
    course_id: str
    lecture_num: int
    lecture_topic: str
    course_title: str

    # ---- 6 维学情画像（比赛要求） ----
    profile: Dict[str, Any]  # {major, grade, foundation, style, goal, weakness}

    # ---- 学习模式 ----
    mode: str  # preview | study | review | challenge

    # ---- 知识库上下文 ----
    knowledge_context: Dict[str, Any]  # RAG 检索结果 + 缓存讲义

    # ---- 各 Agent 产出（并行生成后汇聚） ----
    lecture_doc: Dict[str, Any]       # DocAgent → {title, content}
    mindmap: Dict[str, Any]           # MindmapAgent → {nodes: [...]}
    quiz: Dict[str, Any]              # QuizAgent → {questions: [...]}
    code_example: Dict[str, Any]      # CodeAgent → {content, language}
    extended_reading: Dict[str, Any]  # ReadingAgent → {recommendations: [...]}
    video_script: Dict[str, Any]      # VideoAgent → {scenes: [...]}
    manim_video: Annotated[str | None, _keep_last]     # ManimAgent → MP4 路径
    manim_script: Annotated[str | None, _keep_last]    # ManimAgent → Python 源码
    learning_path: Dict[str, Any]     # PathPlanner → {path: [...]}

    # ---- Agent 协作日志 (多个 Agent 并发写入，需要合并) ----
    messages: Annotated[List[Dict[str, str]], _merge_logs]
    agent_logs: Annotated[List[Dict[str, Any]], _merge_logs]

    # ---- 编排控制 ----
    errors: Annotated[List[Dict[str, Any]], _merge_logs]
    done: Annotated[bool, lambda a, b: b]
