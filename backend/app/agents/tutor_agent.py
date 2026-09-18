"""智能答疑智能体 - LangGraph StateGraph 驱动的 RAG+LLM 答疑系统

StateGraph 流程:
  analyze_question -> search_knowledge -> generate_answer -> verify_answer
                                                                |-- 无幻觉 -> END
                                                                |-- 有幻觉 -> generate_answer(重试1次)
"""
import os
import re
import json
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from ..core.llm import get_llm_client, LLMError
from ..core.database import get_connection
from ..rag.engine import RAGEngine
from ..core.config import settings


def clean_tutor_visible_text(text: str) -> str:
    """Remove provider reasoning and machine-only payloads from tutor output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think\b[^>]*>[\s\S]*?</think>", "", str(text), flags=re.IGNORECASE)
    cleaned = re.sub(r"<analysis\b[^>]*>[\s\S]*?</analysis>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<(?:think|analysis)\b[^>]*>[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*(?:一句话说|简单来说|简而言之|概括来说|总的来说)[，,：:]?\s*", "", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


# ========== LangGraph State ==========

class TutorState(TypedDict, total=False):
    """LangGraph 答疑对话状态

    一次答疑的完整数据流:
    问题 -> 关键词 -> 检索资料 -> 答案 -> 校验 -> (可能重试) -> 追问
    """
    question: str                 # 学生提问
    history: List[Dict[str, str]] # 对话历史
    topic: Optional[str]          # 当前主题(可选)
    keywords: List[str]           # 提取的关键词
    sources: List[Dict]           # 检索到的资料
    answer: str                   # 最终答案
    follow_up: List[str]          # 追问建议
    retry_count: int              # 幻觉校验重试次数
    hallucination_warning: str    # 重试时告诉 LLM 哪里编造了


# ========== Agent 实现 ==========

class MultiAgentTutor:
    """LangGraph StateGraph 驱动的答疑智能体(带反幻觉校验)

    analyze_question -- 提取关键词, 确定检索方向
          |
          v
    search_knowledge -- RAG + 实验库 + 外部知识库
          |
          v
    generate_answer -- LLM 综合资料 -> 答案 + 追问
          |
          v
    verify_answer -- LLM-as-judge: 检查答案是否基于资料
       |        |
    无幻觉    有幻觉(且未重试)
       |        |
       v        v
      END   generate_answer(带警告重试)
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.rag = RAGEngine(str(settings.kb_path))
        self.external_rag = None
        if settings.external_kb_path and os.path.exists(settings.external_kb_path):
            self.external_rag = RAGEngine(settings.external_kb_path)
        self.graph = self._build_graph()

    # ===== 构建 LangGraph =====

    def _build_graph(self) -> StateGraph:
        """构建答疑 StateGraph: 分析 -> 检索 -> 生成 -> 校验 -> (重试|结束)"""
        workflow = StateGraph(TutorState)

        workflow.add_node("analyze_question", self._node_analyze_question)
        workflow.add_node("search_knowledge", self._node_search_knowledge)
        workflow.add_node("generate_answer", self._node_generate_answer)
        workflow.add_node("verify_answer", self._node_verify_answer)

        workflow.set_entry_point("analyze_question")
        workflow.add_edge("analyze_question", "search_knowledge")
        workflow.add_edge("search_knowledge", "generate_answer")
        workflow.add_edge("generate_answer", "verify_answer")

        # 条件路由: 校验通过 -> 结束 / 有幻觉 -> 回到生成节点重试
        workflow.add_conditional_edges(
            "verify_answer",
            self._route_after_verify,
            {
                "generate_answer": "generate_answer",
                END: END,
            }
        )

        return workflow.compile()

    # ===== 节点实现 =====

    async def _node_analyze_question(self, state: TutorState) -> TutorState:
        """节点 1: 分析问题, 提取关键词

        先用规则提取 Python数据分析领域术语,
        规则不足时用中文短语补提关键词.
        """
        question = state.get("question", "")

        spark_kw = [
            "Python", "NumPy", "Pandas", "DataFrame", "Series", "Matplotlib", "Seaborn",
            "Scikit-learn", "ETL", "数据清洗", "可视化", "聚合", "分组", "透视表",
            "缺失值", "异常值", "标准化", "归一化", "特征工程", "线性回归", "分类",
            "聚类", "时间序列", "SQL", "join", "merge", "concat", "groupby",
            "apply", "lambda", "loc", "iloc", "query", "sort_values",
            "drop_duplicates", "fillna", "dropna", "astype", "pivot_table",
            "resample", "rolling", "shift", "melt", "stack", "unstack",
        ]
        found = [kw for kw in spark_kw if kw.lower() in question.lower()]

        if len(found) < 2:
            chinese_words = re.findall(r'[一-鿿]{2,}', question)
            for w in chinese_words[:3]:
                if w not in found:
                    found.append(w)

        state["keywords"] = found if found else [question[:15]]
        return state

    async def _node_search_knowledge(self, state: TutorState) -> TutorState:
        """节点 2: 多路检索资料

        对每个关键词, 搜索 3 个来源:
        1. 本地知识库(RAG)
        2. 实验中心(SQLite)
        3. 外部知识库(可选)
        """
        keywords = state.get("keywords", [])
        question = state.get("question", "")
        history = state.get("history", [])
        retrieval_question = question
        if history and len(question) <= 30:
            previous_user = next((m.get("content", "") for m in reversed(history) if m.get("role") == "user"), "")
            if previous_user:
                retrieval_question = f"{previous_user} {question}"
        collected: List[Dict] = []

        for kw in keywords[:3]:
            # 知识库 RAG
            kb_results = self.rag.search(f"{retrieval_question} {kw}", top_k=3)
            for r in kb_results:
                collected.append({
                    "tool": "search_knowledge",
                    "query": kw,
                    "data": {
                        "title": r.get("title", ""),
                        "content": r.get("content", "")[:2400],
                    },
                })

            # 实验中心
            lab_results = self._search_labs(kw)
            for r in lab_results:
                collected.append({
                    "tool": "search_labs",
                    "query": kw,
                    "data": r,
                })

            # 外部知识库
            if self.external_rag:
                ext_results = self.external_rag.search(kw, top_k=2)
                for r in ext_results:
                    collected.append({
                        "tool": "search_external",
                        "query": kw,
                        "data": {
                            "title": r.get("title", ""),
                            "content": r.get("content", "")[:2400],
                        },
                    })

        # 如果关键词没搜到任何资料, 用原问题全量再搜一次
        if not collected:
            fallback_results = self.rag.search(question[:30], top_k=5)
            for r in fallback_results:
                collected.append({
                    "tool": "search_knowledge",
                    "query": question[:30],
                    "data": {
                        "title": r.get("title", ""),
                        "content": r.get("content", "")[:2400],
                    },
                })

        state["sources"] = collected
        return state

    async def _node_generate_answer(self, state: TutorState) -> TutorState:
        """节点 3: LLM 综合检索结果, 生成答案 + 追问

        如果 state 中有 hallucination_warning, 说明是重试,
        会在 prompt 中追加警告信息.
        """
        question = state.get("question", "")
        history = state.get("history", [])
        topic = state.get("topic")
        sources = state.get("sources", [])
        warning = state.get("hallucination_warning", "")

        answer, follow_up = await self._generate_with_llm(
            question, history, sources, topic, warning
        )

        state["answer"] = clean_tutor_visible_text(answer)
        state["follow_up"] = follow_up
        return state

    async def _node_verify_answer(self, state: TutorState) -> TutorState:
        """节点 4: 反幻觉校验 - LLM-as-judge 检查答案是否基于检索资料

        如果答案中有编造的事实(与 sources 无关的断言),
        设置 hallucination_warning 并触发重试.
        """
        sources = state.get("sources", [])
        answer = state.get("answer", "")
        retry_count = state.get("retry_count", 0)
        state["hallucination_warning"] = ""

        # 没有检索资料时不做校验
        if not sources:
            return state

        # 答案太短也跳过
        if len(answer) < 30:
            return state

        # LLM-as-judge: 用低成本调用检查答案是否 grounded
        verdict = await self._verify_grounding(answer, sources)

        if verdict["has_hallucination"] and retry_count < 1:
            state["retry_count"] = retry_count + 1
            state["hallucination_warning"] = verdict["warning"]
        else:
            state["hallucination_warning"] = ""

        return state

    def _route_after_verify(self, state: TutorState) -> str:
        """条件路由: 有幻觉警告 -> 回炉重造 / 无 -> 结束"""
        if state.get("hallucination_warning"):
            return "generate_answer"
        return END

    # ===== 公开 API =====

    async def answer(self, question: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """答疑入口 - LangGraph 驱动"""
        return await self.answer_with_history(question, [], topic)

    async def answer_with_history(
        self, question: str, history: List[Dict[str, str]], topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """带历史记录的答疑 - LangGraph StateGraph 驱动完整流程

        路径: analyze_question -> search_knowledge -> generate_answer -> verify_answer
        """
        initial_state: TutorState = {
            "question": question,
            "history": history,
            "topic": topic,
            "keywords": [],
            "sources": [],
            "answer": "",
            "follow_up": [],
            "retry_count": 0,
            "hallucination_warning": "",
        }

        result = await self.graph.ainvoke(initial_state)

        return {
            "answer": clean_tutor_visible_text(result.get("answer", "抱歉, 我暂时无法回答这个问题.")),
            "sources": self._format_sources(result.get("sources", [])),
            "follow_up": result.get("follow_up", [])[:3],
            "tool_log": [f"检索 {len(result.get('sources', []))} 条资料"],
        }

    # ===== 反幻觉校验 =====

    async def _verify_grounding(
        self, answer: str, sources: List[Dict]
    ) -> Dict[str, Any]:
        """LLM-as-judge: 检查答案的事实断言是否能追溯到检索资料

        返回 {"has_hallucination": bool, "warning": str}
        """
        sources_text = self._summarize_sources(sources)[:1500]

        check_prompt = f"""你是一个严格的事实校验员. 检查下面的「答案」是否完全基于「参考资料」.

如果答案中有:
- 概念定义/技术细节/版本号/API 名称等不在资料中 -> 标记为幻觉
- 凭空编造的代码示例 -> 标记为幻觉
- 与资料矛盾的说法 -> 标记为幻觉

用 JSON 格式回复:
{{"has_hallucination": true或false, "warning": "如果有幻觉, 指出具体什么问题, 要简短"}}

答案:
{answer[:800]}

参考资料:
{sources_text}"""

        try:
            resp = await self.llm.chat(
                [{"role": "system",
                  "content": "你是事实校验员. 只输出 JSON, 不要任何多余文字."},
                 {"role": "user", "content": check_prompt}],
                temperature=0.0, max_tokens=200
            )

            m = re.search(r'\{[\s\S]*\}', resp)
            if m:
                verdict = json.loads(m.group())
                return {
                    "has_hallucination": bool(verdict.get("has_hallucination", False)),
                    "warning": str(verdict.get("warning", "")),
                }
        except Exception:
            pass

        return {"has_hallucination": False, "warning": ""}

    # ===== 内部方法 =====

    def _search_labs(self, query: str) -> List[Dict]:
        """搜索实验中心数据库"""
        try:
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT title, topics, source_path FROM labs "
                    "WHERE title LIKE ? OR topics LIKE ? LIMIT 3",
                    (f"%{query}%", f"%{query}%")
                ).fetchall()
            return [
                {"title": r["title"], "topics": r["topics"], "source": r["source_path"]}
                for r in rows
            ]
        except Exception:
            return []

    async def _generate_with_llm(
        self,
        question: str,
        history: List[Dict],
        sources: List[Dict],
        topic: Optional[str],
        warning: str = "",
    ) -> tuple[str, List[str]]:
        """一次 LLM 调用: 结合检索资料 + 对话历史 -> 答案 + 追问

        warning: 上一轮校验发现的幻觉问题, 追加到 prompt 中强制修正
        """
        context = self._summarize_sources(sources)
        history_text = self._format_history(history)

        warning_block = ""
        if warning:
            warning_block = f"""
## !! 上一轮回答校验未通过 - 必须修正
{ warning }

修正要求:
- 只使用上面「参考资料」中的信息回答
- 如果资料不足以回答, 明确说明“当前课程资料未覆盖该问题”，不要补充课程外知识
- 不要编造任何不在参考资料中的概念/定义或数据
"""

        prompt = f"""你是 Python数据分析课程的答疑专家. 回答要精简, 直击要点.

## 回答要求
1. 直接回答问题，2-4句话即可，不要使用“一句话说”“简单来说”等开场套话
2. 只有必要时才给代码示例, 代码要短
3. 不要展开长篇解释
4. 禁止用 Markdown 格式(不用**/##/|表格|等)
{warning_block}
## 对话历史
{history_text if history_text else "(新问题)"}

## 问题
{question}

## 课程参考资料
{context if context else "(当前课程资料中未检索到与问题直接相关的内容)"}

## 回答要求
1. 直接给出核心结论，不要添加“一句话说”等引导语
2. 展开解释(概念+原理+代码示例)
3. 有代码用 Python, 中文注释
4. 资料不足时只说明课程资料未覆盖，不要使用课程外知识补充
5. 末尾标注实际使用的课程资料来源

## 格式规则(严格遵守)
- 绝对禁止 Markdown: 不要用 ** 加粗/不要用 ## 标题/不要用 | 表格/不要用 --- 分隔线
- 当问题涉及流程/架构/关系时，可以用 ```mermaid ... ``` 块提供可视化图表(flowchart LR/sequenceDiagram/classDiagram 均可)
- 用自然段落表达, 用空行分隔不同要点
- 需要对比时用文字描述, 不要画表格
- 代码示例直接写, 每行代码前加两个空格缩进即可, 不要用三个反引号
- 用 ---FOLLOWUP--- 分隔答案和追问

示例:
Pandas DataFrame的groupby操作按照指定列分组,然后对每组应用聚合函数(如mean/sum/count),返回汇总后的新DataFrame.

窄依赖是每个父分区最多被一个子分区使用, 不需要Shuffle. 举例来说, map和filter操作产生窄依赖, 而groupByKey产生宽依赖.

---FOLLOWUP---
宽依赖对 Stage 划分有什么影响
实际业务中如何避免不必要的宽依赖"""

        try:
            resp = await self.llm.chat(
                [{"role": "system",
                  "content": "你是 Python数据分析课程答疑专家. 回答要精简: 2-4句话直击要点, 不要长篇大论. 禁止Markdown格式."},
                 {"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=400
            )
            if "---FOLLOWUP---" in resp:
                parts = resp.split("---FOLLOWUP---", 1)
                answer = clean_tutor_visible_text(self._clean_markdown(parts[0].strip()))
                follow_ups = [
                    line.strip() for line in parts[1].strip().split('\n')
                    if line.strip() and len(line.strip()) > 3
                ][:3]
                return answer, follow_ups if follow_ups else [
                    "能详细解释一下吗?", "有没有代码示例?"
                ]
            return clean_tutor_visible_text(self._clean_markdown(resp)), ["能详细解释一下吗?", "有没有代码示例?"]
        except Exception as e:
            return f"抱歉, 暂时无法回答. {str(e)}", []

    def _summarize_sources(self, sources: List[Dict]) -> str:
        """将检索到的资料整理成 LLM 可读的文本"""
        if not sources:
            return ""
        lines = []
        for s in sources:
            tool = s.get("tool", "unknown")
            data = s.get("data", {})
            if isinstance(data, list):
                lines.append(f"课程资料（{tool}）：{len(data)} 条结果")
                for item in data[:3]:
                    title = item.get("title", "") if isinstance(item, dict) else ""
                    content = str(item.get("content", "")) if isinstance(item, dict) else str(item)
                    lines.append(f"    - {title}: {content[:200]}")
            elif isinstance(data, dict):
                lines.append(f"课程资料：{data.get('title', '')}")
                lines.append(f"    {str(data.get('content', ''))[:2400]}")
        return "\n".join(lines)

    def _format_sources(self, sources: List[Dict]) -> List[Dict]:
        """格式化来源列表, 去重后返回"""
        formatted = []
        seen = set()
        for s in sources:
            data = s.get("data", {})
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = item.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    formatted.append({
                        "title": title,
                        "source_path": item.get("source", item.get("source_path", "")),
                        "content": str(item.get("content", ""))[:200],
                    })
        # Retrieval is ranked by relevance. Expose only the strongest source
        # so the UI does not imply that lower-ranked, unused lectures support
        # the answer.
        return formatted[:1]

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """格式化对话历史"""
        if not history or len(history) <= 1:
            return ""
        recent = history[-6:]
        return "\n".join(
            f"{'学生' if m.get('role') == 'user' else '助手'}: {m.get('content', '')[:200]}"
            for m in recent
        )

    def _clean_markdown(self, text: str) -> str:
        """清除 LLM 回复中的所有 Markdown 格式"""
        text = re.sub(
            r'```[\s\S]*?```',
            lambda m: '\n'.join(m.group().replace('```', '').strip().split('\n')[1:]).strip(),
            text
        )
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\-*]{3,}\s*$', '', text, flags=re.MULTILINE)
        lines = text.split('\n')
        clean_lines = []
        in_table = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                if re.match(r'^\|[\s\-:|]+\|$', stripped):
                    in_table = True
                    continue
                if in_table or '|' in stripped[1:-1]:
                    cells = [c.strip() for c in stripped[1:-1].split('|')]
                    clean_lines.append(': '.join(cells))
                    in_table = True
                    continue
            in_table = False
            line = re.sub(r'^(\s*)[-*]\s+', r'\1* ', line)
            clean_lines.append(line)
        text = '\n'.join(clean_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


# ===== 向后兼容别名 & 工厂函数 =====

TutorAgent = MultiAgentTutor


def get_tutor_agent() -> MultiAgentTutor:
    return MultiAgentTutor()
