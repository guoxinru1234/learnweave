"""RAG 检索引擎.

Current implementation uses a local hybrid retrieval path:
- ChromaDB when a local `knowledge-base/.chroma` index exists.
- Keyword scoring over generated `knowledge-base/assets/chunks.jsonl`.
"""
from __future__ import annotations

from typing import List
import hashlib
import json
import math
import os
import re


class HashEmbeddingFunction:
    """Must match scripts/ingest_course_assets.py for local Chroma indexes."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def name(self) -> str:
        return f"learnmate-hash-{self.dimensions}"

    def __call__(self, input):
        return [self.embed(text) for text in input]

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())
        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

class RAGEngine:
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.documents = []
        self.index = {}
        self._catalog: dict[str, dict] = {}
        self._chroma_collection = None
        # P2: 知识点体系（knowledge_points.json / skill_tree.json）
        self._knowledge_points: list[dict] = []
        self._kp_by_id: dict[str, dict] = {}
        self._kp_by_lesson: dict[int, list[dict]] = {}
        self._skill_tree: dict = {}
        self._load_knowledge_base()
        self._load_catalog()
        self._load_knowledge_points()
        self._load_chroma()

    def _load_knowledge_points(self):
        """加载 P1 建立的知识点体系，建立 knowledge_id / lesson 索引。"""
        kp_path = os.path.join(self.kb_path, "knowledge_points.json")
        if os.path.exists(kp_path):
            try:
                with open(kp_path, encoding="utf-8") as f:
                    self._knowledge_points = json.load(f)
                for kp in self._knowledge_points:
                    kid = kp.get("knowledge_id", "")
                    if kid:
                        self._kp_by_id[kid] = kp
                    for lesson in kp.get("source_lessons", []):
                        self._kp_by_lesson.setdefault(lesson, []).append(kp)
            except Exception:
                pass
        sk_path = os.path.join(self.kb_path, "skill_tree.json")
        if os.path.exists(sk_path):
            try:
                with open(sk_path, encoding="utf-8") as f:
                    self._skill_tree = json.load(f)
            except Exception:
                pass

    def _load_catalog(self):
        catalog_path = os.path.join(self.kb_path, "assets", "catalog.json")
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, encoding="utf-8-sig") as f:
                    items = json.load(f)
                for item in items:
                    aid = item.get("id", "")
                    if aid:
                        self._catalog[aid] = item
            except Exception:
                pass

    def _load_knowledge_base(self):
        index_path = os.path.join(self.kb_path, "index.json")
        if os.path.exists(index_path):
            with open(index_path, encoding="utf-8") as f:
                self.index = json.load(f)
            for lec in self.index.get("lectures", []):
                md_path = os.path.join(self.kb_path, lec["dir"], "lecture.md")
                if os.path.exists(md_path):
                    with open(md_path, encoding="utf-8") as f:
                        content = f.read()
                    self.documents.append({
                        "id": f"lecture-{int(lec['id']):02d}",
                        "asset_id": f"lecture-{int(lec['id']):02d}",
                        "title": lec["title"],
                        "category": "lecture",
                        "source_path": os.path.relpath(md_path, os.path.dirname(self.kb_path)),
                        "topics": [],
                        "lecture_ids": [int(lec["id"])],
                        "text": content,
                    })
        chunks_path = os.path.join(self.kb_path, "assets", "chunks.jsonl")
        if os.path.exists(chunks_path):
            with open(chunks_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.documents.append(json.loads(line))

    def _load_chroma(self):
        chroma_path = os.path.join(self.kb_path, ".chroma")
        if not os.path.isdir(chroma_path):
            return
        try:
            import chromadb
            client = chromadb.PersistentClient(path=chroma_path)
            self._chroma_collection = client.get_collection(
                "learnmate_course_assets",
                embedding_function=HashEmbeddingFunction(),
            )
        except Exception:
            self._chroma_collection = None

    def _tokens(self, query: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{1,2}", query.lower())

    def _keyword_score(self, query: str, doc: dict) -> float:
        q = query.lower()
        text = (doc.get("text") or "").lower()
        title = (doc.get("title") or "").lower()
        source = (doc.get("source_path") or "").lower()
        score = 0.0
        if q and q in title:
            score += 20
        if q and q in text:
            score += 8
        if q and q in source:
            score += 4
        for token in self._tokens(query):
            if not token:
                continue
            if token in title:
                score += 6
            if token in source:
                score += 3
            count = text.count(token)
            if count:
                score += min(5, count)
        return score

    def _snippet(self, query: str, text: str, size: int = 600) -> str:
        lower = text.lower()
        positions = [lower.find(token) for token in self._tokens(query) if lower.find(token) >= 0]
        start = max(0, min(positions) - 80) if positions else 0
        snippet = text[start : start + size].strip()
        return re.sub(r"\s+", " ", snippet)

    def _format_result(self, doc: dict, score: float, query: str) -> dict:
        text = doc.get("text") or ""
        return {
            "id": doc.get("id") or doc.get("asset_id"),
            "asset_id": doc.get("asset_id") or doc.get("id"),
            "title": doc.get("title", ""),
            "category": doc.get("category", "unknown"),
            "source_path": doc.get("source_path", ""),
            "topics": doc.get("topics", []),
            "lecture_ids": doc.get("lecture_ids", []),
            "snippet": self._snippet(query, text, size=2400),
            # Tutor and other agents consume `content`; keep the retrieved
            # evidence snippet available instead of returning title-only hits.
            "content": self._snippet(query, text, size=2400),
            "score": round(score, 4),
        }

    def _keyword_search(self, query: str, top_k: int) -> list[dict]:
        scored = []
        for doc in self.documents:
            score = self._keyword_score(query, doc)
            # 过滤弱相关：score < 8 视为无关（避免"无意义 query"返回垃圾结果）
            if score >= 8:
                scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._format_result(doc, score, query) for score, doc in scored[:top_k]]

    def _chroma_search(self, query: str, top_k: int) -> list[dict]:
        if not self._chroma_collection:
            return []
        try:
            data = self._chroma_collection.query(query_texts=[query], n_results=top_k)
        except Exception:
            return []
        results = []
        ids = data.get("ids", [[]])[0]
        docs = data.get("documents", [[]])[0]
        metadatas = data.get("metadatas", [[]])[0]
        distances = data.get("distances", [[]])[0] if data.get("distances") else [0] * len(ids)
        for idx, doc_id in enumerate(ids):
            meta = metadatas[idx] or {}
            text = docs[idx] if idx < len(docs) else ""
            distance = distances[idx] if idx < len(distances) else 0
            results.append({
                "id": doc_id,
                "asset_id": meta.get("asset_id", ""),
                "title": meta.get("title", ""),
                "category": meta.get("category", ""),
                "source_path": meta.get("source_path", ""),
                "topics": [x for x in meta.get("topics", "").split(",") if x],
                "lecture_ids": [int(x) for x in meta.get("lecture_ids", "").split(",") if x.isdigit()],
                "snippet": self._snippet(query, text, size=2400),
                "content": self._snippet(query, text, size=2400),
                "score": round(1 / (1 + float(distance)), 4),
            })
        return results

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """搜索相关知识，优先 ChromaDB，本地关键词检索兜底并补充。"""
        merged: list[dict] = []
        seen: set[str] = set()
        for result in self._chroma_search(query, top_k):
            key = result.get("asset_id") or result["id"]
            if key not in seen:
                seen.add(key)
                merged.append(result)
        for result in self._keyword_search(query, top_k * 2):
            key = result.get("asset_id") or result["id"]
            if key not in seen:
                seen.add(key)
                merged.append(result)
            if len(merged) >= top_k:
                break
        return merged[:top_k]

    def _format_evidence(self, doc: dict, score: float, query: str) -> dict:
        """将检索结果格式化为结构化证据"""
        asset_id = doc.get("asset_id") or doc.get("id", "")
        catalog_entry = self._catalog.get(asset_id, {})
        # 修复 content 空 bug：keyword/chroma 检索结果只带 snippet 不带 text，
        # 导致 evidence.content 恒为空。这里通过 asset_id 反查 self.documents
        # 取回真实知识正文，兜底用 snippet。
        text = doc.get("text") or ""
        if not text:
            for d in self.documents:
                if (d.get("asset_id") or d.get("id")) == asset_id:
                    text = d.get("text") or ""
                    break
        if not text:
            text = doc.get("snippet") or ""
        title = doc.get("title") or catalog_entry.get("title", "")
        source_path = doc.get("source_path") or catalog_entry.get("source_path", "")
        category = doc.get("category") or catalog_entry.get("category", "unknown")
        lecture_ids = doc.get("lecture_ids") or catalog_entry.get("lecture_ids", [])
        topics = doc.get("topics") or catalog_entry.get("topics", [])
        chunk_id = doc.get("chunk_id") or doc.get("id") or asset_id

        # 权威等级: lecture > case > exercise > manual > dataset > unknown
        auth_map = {"lecture": 5, "case": 4, "exercise": 3, "manual": 3, "dataset": 2}
        authority = auth_map.get(category, 1)

        # 定位器: 讲次号
        locator = f"lecture-{lecture_ids[0]:02d}" if lecture_ids else (source_path or "")

        # P2: 关联知识点体系。asset_id 格式 "lecture-16" → 讲次号 16，
        # 反查 knowledge_points.json 得到真正的 knowledge_id / skill_domain。
        lesson_num = None
        m = re.match(r"lecture-(\d+)", asset_id)
        if m:
            lesson_num = int(m.group(1))
        kp_list = self._kp_by_lesson.get(lesson_num, []) if lesson_num is not None else []
        kp = kp_list[0] if kp_list else None

        return {
            "knowledge_id": kp["knowledge_id"] if kp else asset_id,
            "skill_domain": kp["skill_domain"] if kp else "",
            "source_lesson": lesson_num,
            "source_id": asset_id,
            "source_title": title,
            "source_type": category,
            "chunk_id": chunk_id,
            "content": self._snippet(query, text) if text else "",
            "knowledge_points": (kp.get("knowledge_points") or topics[:5]) if kp else topics[:5],
            "locator": locator,
            "relevance_score": round(score, 4),
            "source_url": "",
            "source_path": source_path,
            "authority_level": authority,
        }

    def search_evidence(self, query: str, top_k: int = 5) -> list[dict]:
        """搜索并返回结构化证据列表。

        优先 ChromaDB 向量检索 + 关键词兜底。
        无结果时返回空列表 []（不伪造）。
        """
        merged: list[dict] = []
        seen: set[str] = set()
        for result in self._chroma_search(query, top_k):
            key = result.get("asset_id") or result["id"]
            if key not in seen:
                seen.add(key)
                merged.append(result)
        for result in self._keyword_search(query, top_k * 2):
            key = result.get("asset_id") or result["id"]
            if key not in seen:
                seen.add(key)
                merged.append(result)
            if len(merged) >= top_k:
                break
        # Format as evidence
        evidence = []
        for doc in merged[:top_k]:
            evidence.append(self._format_evidence(
                doc, doc.get("score", 0), query
            ))
        return evidence

    def search_knowledge_points(self, query: str, skill_domain: str = None,
                                knowledge_id: str = None, top_k: int = 5) -> list[dict]:
        """按知识点检索（P2.1）。

        支持 query + skill_domain + knowledge_id 过滤，返回匹配的知识点。
        匹配逻辑：knowledge_points 标签 + title 关键词打分，不依赖 embedding。
        """
        if knowledge_id:
            kp = self._kp_by_id.get(knowledge_id)
            return [kp] if kp else []

        if not self._knowledge_points:
            return []

        q_tokens = set(self._tokens(query.lower())) if query else set()

        scored = []
        for kp in self._knowledge_points:
            if skill_domain and kp.get("skill_domain") != skill_domain:
                continue
            score = 0.0
            title = (kp.get("title") or "").lower()
            points = [str(p).lower() for p in (kp.get("knowledge_points") or [])]
            if query and query.lower() in title:
                score += 20
            for t in q_tokens:
                if any(t in p for p in points):
                    score += 8
                if t in title:
                    score += 6
            if score > 0:
                scored.append((score, kp))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [kp for _, kp in scored[:top_k]]

    def get_context(self, query: str) -> str:
        """获取查询相关的知识上下文"""
        results = self.search(query)
        if not results:
            return ""
        contexts = []
        docs_by_id = {doc.get("id"): doc for doc in self.documents}
        for result in results:
            doc = docs_by_id.get(result["id"])
            if doc and doc.get("text"):
                contexts.append(f"【{result['title']}】\n{doc['text'][:2000]}")
            elif result.get("snippet"):
                contexts.append(f"【{result['title']}】\n{result['snippet']}")
        return "\n\n".join(contexts)
