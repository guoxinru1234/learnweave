"""拓展阅读材料 Agent（比赛要求新资源类型）。

职责：通过 RAG 检索 + LLM 总结，为学生推荐个性化的拓展阅读材料。
每份推荐包含：标题、推荐理由、难度等级、与当前学习内容的关联点。

这是比赛要求的 5 种资源类型之一：拓展阅读材料。
"""

import json
import re
from typing import Dict, Any, List

from .base import BaseAgent
from ..rag.engine import RAGEngine
from ..core.config import settings

READING_SYSTEM_PROMPT = """你是一位学术研究指导专家，专注于为大学生推荐和总结拓展阅读材料。

你的职责是：
1. 从知识库中检索与当前主题相关的资料
2. 筛选出适合学生当前水平的材料
3. 为每份材料撰写简短的推荐理由
4. 标注难度等级（入门 / 进阶 / 研究）
5. 指出材料与当前学习内容的关联点

每份推荐 50-80 字，简洁有力，激发学生的阅读兴趣。
"""


class ReadingAgent(BaseAgent):
    """拓展阅读 Agent —— RAG 检索 + LLM 总结推荐。"""

    def __init__(self):
        super().__init__("ReadingAgent", READING_SYSTEM_PROMPT)
        self.rag = RAGEngine(str(settings.kb_path))

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("lecture_topic", "")
        profile = state.get("profile", {})
        mode = state.get("mode", "study")
        domain_context = state.get("domain_context", {})

        # Step 1: RAG 检索（统一用 search_evidence，返回标准 evidence 字段）
        sources = self.rag.search_evidence(topic, top_k=8)

        # Step 2: 按 mode 过滤数量
        filtered = self._filter_by_mode(sources, mode)

        # Step 3: LLM 为每份来源生成推荐理由
        recommendations = await self._summarize_sources(
            filtered, topic, profile, domain_context
        )

        self.log(f"拓展阅读生成完成，{len(recommendations)} 条推荐")
        return {
            "extended_reading": {
                "topic": topic,
                "recommendations": recommendations,
                "total_sources": len(sources),
                "mode": mode,
            }
        }

    def _filter_by_mode(self, sources: List[dict], mode: str) -> List[dict]:
        limits = {"preview": 2, "study": 4, "review": 4, "challenge": 6}
        return sources[:limits.get(mode, 4)]

    async def _summarize_sources(self, sources: List[dict], topic: str,
                                 profile: dict, domain_context: dict = None) -> List[dict]:
        """LLM 为每份资料生成推荐摘要。"""
        recommendations = []
        # 个性化:优先领域技能画像 level,回退 profile.foundation
        level = (domain_context or {}).get("level")
        foundation = {"basic": "零基础", "intermediate": "中等", "advanced": "进阶"}.get(
            level, profile.get("foundation", "中等"))

        for src in sources:
            title = src.get("source_title") or src.get("title", "相关资料")
            snippet = src.get("content", "")[:500]

            prompt = f"""为以下资料撰写阅读推荐。

主题：{topic}
资料标题：{title}
内容摘要：{snippet}
学生水平：{foundation}

请以 JSON 格式输出：
{{"title": "资料标题", "summary": "推荐理由（50-80字）", "difficulty": "入门/进阶/研究", "relevance": "与当前学习内容的关联（20-30字）"}}
只输出 JSON。"""

            try:
                raw = await self._call_llm(prompt, temperature=0.5, max_tokens=300)
                parsed = self._parse_json(raw)
                if parsed:
                    recommendations.append(parsed)
            except Exception as e:
                self.log(f"推荐生成失败 ({title}): {e}")
                recommendations.append({
                    "title": title,
                    "summary": "值得深入了解的拓展资料",
                    "difficulty": "进阶",
                    "relevance": f"与 {topic} 相关",
                })

        return recommendations

    def _parse_json(self, raw: str) -> dict | None:
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            # 尝试找第一个 JSON 对象
            m = re.search(r'\{[^{}]*"title"[^{}]*\}', raw)
            if m:
                return json.loads(m.group())
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            return None
