"""ProfessionalAuditAgent — 8维度结构化审核。
每项 issue 可定位、可修复、可复审，供 FixAgent 直接消费。
"""
import json, re, uuid
from typing import Dict, Any, List
from .base import BaseAgent

AUDIT_SYSTEM_PROMPT = """你是专业知识审核专家。审核AI生成的内容，基于提供的知识库证据，给出评分和改进建议。

审核维度（8项）：
1. 知识依据：内容是否有知识库证据支撑
2. 事实冲突：内容是否与知识库证据矛盾
3. 无来源事实：是否出现知识库未支持的事实断言（幻觉）
4. 准确性：概念、定义、API 是否准确
5. 完整性：核心知识点是否覆盖
6. 代码正确性：Python 代码是否有明显错误
7. 难度匹配：内容难度是否符合学习者画像
8. 引用完整性：是否遗漏必要的知识来源引用

只输出如下JSON，不要加任何解释文字：
{"overall_confidence":85,"issues":[]}

评分: 90+=优秀, 75-89=良好, 60-74=一般, <60=不合格
问题项格式: {"severity":"major","description":"具体问题描述","suggested_fix":"建议修改方案"}
没有问题时 issues 为空数组 []
"""


class AuditAgent(BaseAgent):
    """专业审核 Agent — 8维度结构化审核"""

    def __init__(self):
        super().__init__("ProfessionalAuditAgent", AUDIT_SYSTEM_PROMPT)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """审核所有已生成内容，返回结构化审核报告（并行处理各资源项）。"""
        import asyncio

        items = self._extract_items(state)
        profile = state.get("profile", {})
        context = state.get("knowledge_context", {})
        evidence = context.get("sources", [])
        # 统一字段标准：evidence 字段为 knowledge_id/skill_domain/source_title/content。
        # 把知识点标识 + 正文摘要拼进引用，让审核能判断"核心知识点是否覆盖"。
        ev_refs = []
        for e in (evidence or [])[:5]:
            title = e.get("source_title") or e.get("title", "")
            kid = e.get("knowledge_id", "")
            domain = e.get("skill_domain", "")
            points = e.get("knowledge_points", [])
            content = (e.get("content") or "")[:200]
            label = f"[{domain}][{kid}] {title}" if domain and kid else title
            point_hint = f" 核心点={points}" if points else ""
            ev_refs.append(f"{label}{point_hint}: {content}")

        all_issues: List[dict] = []
        confidences: List[int] = []

        async def _audit_one(item: dict) -> tuple:
            """审核单个资源项，返回 (issues, confidence)。"""
            prompt = self._build_prompt(item, profile, ev_refs)
            try:
                raw = await self._call_llm(prompt, temperature=0.3, max_tokens=800)
                parsed = self._parse_json(raw)
                if parsed and "overall_confidence" in parsed:
                    confidence = int(parsed.get("overall_confidence", 50))
                    item_issues = []
                    for iss in parsed.get("issues", []):
                        iss.setdefault("issue_id", f"iss-{uuid.uuid4().hex[:8]}")
                        iss.setdefault("resource_id", item["type"])
                        iss.setdefault("status", "open")
                        iss.setdefault("evidence_refs", [])
                        item_issues.append(iss)
                    return (item_issues, confidence)
                return ([], 50)
            except Exception:
                return ([], 50)

        # 并行审核所有资源项
        results = await asyncio.gather(
            *[_audit_one(item) for item in items],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                confidences.append(50)
                continue
            item_issues, confidence = r
            all_issues.extend(item_issues)
            confidences.append(confidence)

        overall = round(sum(confidences) / len(confidences)) if confidences else 50
        passed = overall >= 75

        self.log(f"Audit: {len(all_issues)} issues, confidence={overall}%, passed={passed}")

        return {
            "audit_report": {
                "overall_confidence": overall,
                "passed": passed,
                "total_issues": len(all_issues),
                "critical_issues": len([i for i in all_issues if i.get("severity") == "critical"]),
                "items_audited": len(items),
                "issues": all_issues,
            },
            "audit_passed": passed,
        }

    def _extract_items(self, state: dict) -> list[dict]:
        items = []
        for key, res_type in [("lecture_doc", "lecture_doc"), ("code_example", "code"),
                               ("mindmap", "mindmap"), ("quiz", "quiz"),
                               ("extended_reading", "reading")]:
            val = state.get(key)
            if val:
                content = ""
                if isinstance(val, dict):
                    content = val.get("content", "") or json.dumps(val.get("nodes", []), ensure_ascii=False)
                    if key == "quiz":
                        content = json.dumps(val.get("questions", []), ensure_ascii=False)[:1500]
                    if key == "code_example":
                        content = val.get("content", "") or json.dumps(val, ensure_ascii=False)
                items.append({"type": res_type, "content": str(content)[:1500]})
        return items

    def _build_prompt(self, item: dict, profile: dict, ev_refs: list) -> str:
        profile_str = json.dumps({k: v for k, v in profile.items() if isinstance(v, (int, float))}, ensure_ascii=False) if profile else "无"
        ev_str = "\n".join(f"- {r}" for r in ev_refs) if ev_refs else "无"
        return (
            f"审核以下 {item['type']} 类型内容:\n\n"
            f"【内容】\n{item['content']}\n\n"
            f"【学习者画像】\n{profile_str}\n"
            f"【知识库证据】\n{ev_str}\n\n"
            f"请从8维度审核，输出 JSON。"
        )

    def _parse_json(self, raw: str) -> dict | None:
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            return None


def get_audit_agent() -> AuditAgent:
    return AuditAgent()
