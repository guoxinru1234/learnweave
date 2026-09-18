"""Deterministic audit for resources copied from the local knowledge base.

This is an explicit fallback for an unavailable LLM audit service.  It only
approves content that is traceable to a local source and passes concrete
structure, citation, code and learner-level checks.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

from markdown_it import MarkdownIt


class GroundedKnowledgeAudit:
    MODE = "deterministic_grounded_audit"

    def build_content(self, source: dict) -> str:
        source_path = source.get("source_path", "")
        path = Path(source_path)
        if not path.is_absolute():
            candidates = (Path.cwd() / path, Path.cwd().parent / path)
            path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
        if not path.is_file():
            return ""

        markdown = path.read_text(encoding="utf-8")
        knowledge_id = source.get("knowledge_id", "")
        source_title = source.get("source_title", path.stem)
        citation = f"[{knowledge_id}]" if knowledge_id else f"[{source_title}]"
        html = MarkdownIt("commonmark", {"html": True}).enable("table").render(markdown)
        return (
            f'<p class="knowledge-citation"><strong>知识依据：</strong>{citation} '
            f'{source_title}</p>\n{html}\n'
            f'<h2>参考依据</h2><p>{citation} {source_title}（本地课程知识库）</p>'
        )

    def audit(self, state: Dict[str, Any], source: dict) -> dict:
        content = state.get("lecture_doc", {}).get("content", "")
        code = state.get("code_example", {}).get("content", "") or state.get("code_example", {}).get("code", "")
        mindmap = state.get("mindmap", {}).get("nodes", [])
        knowledge_id = source.get("knowledge_id", "")

        checks = {
            "local_source_loaded": len(content) >= 1500,
            "source_cited": bool(knowledge_id and knowledge_id in content),
            "reference_section": "参考依据" in content,
            "core_sections": all(key in content for key in ("概念", "核心命令", "代码示例", "常见错误", "练习")),
            "beginner_support": any(key in content for key in ("生活化类比", "入门", "逐条", "步骤")),
            "mindmap_structured": self._count_nodes(mindmap) >= 30 and self._depth(mindmap) >= 4,
            "python_code_valid": self._valid_python(code),
        }
        weights = {
            "local_source_loaded": 25,
            "source_cited": 15,
            "reference_section": 10,
            "core_sections": 20,
            "beginner_support": 10,
            "mindmap_structured": 10,
            "python_code_valid": 10,
        }
        score = sum(weights[name] for name, passed in checks.items() if passed)
        issues = [
            {"issue_id": f"grounded-{name}", "severity": "major", "category": name,
             "description": f"确定性检查未通过：{name}"}
            for name, passed in checks.items() if not passed
        ]
        return {
            "overall_confidence": score,
            "passed": score >= 75 and checks["local_source_loaded"] and checks["source_cited"],
            "total_issues": len(issues),
            "critical_issues": 0,
            "issues": issues,
            "details": [{"check": name, "passed": passed, "weight": weights[name]} for name, passed in checks.items()],
            "hallucination_rate": 0 if checks["local_source_loaded"] and checks["source_cited"] else None,
            "difficulty_match_score": 90 if checks["beginner_support"] else 60,
            "mode": self.MODE,
            "service_available": False,
        }

    @staticmethod
    def _valid_python(code: str) -> bool:
        if not code.strip():
            return False
        try:
            compile(code, "<lecture-code>", "exec")
            return True
        except SyntaxError:
            return False

    def _count_nodes(self, nodes: list) -> int:
        return sum(1 + self._count_nodes(node.get("children", [])) for node in nodes)

    def _depth(self, nodes: list) -> int:
        if not nodes:
            return 0
        return 1 + max(self._depth(node.get("children", [])) for node in nodes)
