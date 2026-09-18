"""
KnowledgeRetrievalAgent — 知识库检索与结构化证据整理。

将检索结果从普通字符串升级为结构化证据，供生成 Agent 和审核 Agent 共同使用。
"""
from ..rag.engine import RAGEngine
from ..core.config import settings


class KnowledgeRetrievalAgent:
    """知识库检索 Agent — 返回结构化证据列表。

    每条 evidence 包含:
      source_id, source_title, source_type, chunk_id, content,
      knowledge_points, locator, relevance_score, source_path, authority_level

    无结果时返回 empty evidence（空列表），不伪造来源。
    """

    def __init__(self):
        self._engine = RAGEngine(str(settings.kb_path))

    def retrieve(self, topic: str, top_k: int = 5) -> list[dict]:
        """检索知识库，返回结构化证据列表。无结果时返回 []。"""
        if not topic or not topic.strip():
            return []
        return self._engine.search_evidence(topic, top_k=top_k)

    def retrieve_knowledge_points(self, topic: str, skill_domain: str = None,
                                  knowledge_id: str = None, top_k: int = 5) -> list[dict]:
        """检索知识点（P2.1）。返回匹配的 knowledge point 列表。"""
        if not topic or not topic.strip():
            return []
        return self._engine.search_knowledge_points(
            topic, skill_domain=skill_domain, knowledge_id=knowledge_id, top_k=top_k
        )

    def retrieve_with_knowledge(self, topic: str, skill_domain: str = None,
                                top_k: int = 5) -> dict:
        """检索知识点 + evidence（P2 核心入口）。

        返回 {"knowledge_points": [...], "evidence": [...]}。
        """
        kps = self.retrieve_knowledge_points(topic, skill_domain=skill_domain, top_k=top_k)
        evidence = self.retrieve(topic, top_k=top_k)
        return {"knowledge_points": kps, "evidence": evidence}

    def execute(self, state: dict) -> dict:
        """兼容编排器接口 — 从 state 中提取 topic 进行检索"""
        topic = state.get("lecture_topic", "")
        skill_domain = state.get("skill_domain")
        knowledge_points = self.retrieve_knowledge_points(topic, skill_domain=skill_domain)
        evidence = self.retrieve(topic)
        return {
            "sources": evidence,
            "knowledge_points": knowledge_points,
            "topic": topic,
            "evidence_count": len(evidence),
            "empty": len(evidence) == 0,
        }


def get_knowledge_agent() -> KnowledgeRetrievalAgent:
    return KnowledgeRetrievalAgent()
