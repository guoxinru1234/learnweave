"""FixAgent — 按 issue_id 逐项修订，追踪每个问题的 resolved/unresolved 状态。"""
from .base import BaseAgent
from ..core.llm import get_llm_client

FIX_SYSTEM_PROMPT = """你是内容修正专家。根据审核问题逐项修订教学内容。直接输出修正后的Markdown内容，不要JSON。"""


class FixAgent(BaseAgent):
    """内容修正 Agent — 逐 issue 修订 + 状态追踪"""

    def __init__(self):
        super().__init__("FixAgent", FIX_SYSTEM_PROMPT)
        self._llm = get_llm_client()

    async def fix(self, content: str, issues: list[dict]) -> tuple[str, bool]:
        """根据审核问题修正内容（兼容旧接口）。"""
        if not content or not issues:
            return content, False
        issues_text = "\n".join(
            f"- [{i.get('severity','minor')}] [{i.get('issue_id','?')}] {i.get('location','')}: "
            f"{i.get('description', i.get('problem',''))}"
            f"\n  suggested_fix: {i.get('suggested_fix', i.get('fix',''))}"
            for i in issues[:5]
        )
        prompt = (
            f"修正以下内容的问题：\n\n"
            f"【原内容】\n{content[:8000]}\n\n"
            f"【审核问题】\n{issues_text}\n\n"
            f"输出修正后的完整Markdown。"
        )
        try:
            fixed = await self._call_llm(prompt, temperature=0.4, max_tokens=2048)
            if fixed and len(fixed) > 100:
                return fixed, True
        except Exception:
            pass
        return content, False

    async def fix_with_tracking(self, content: str, issues: list[dict],
                                evidence: list[dict] = None) -> dict:
        """按 issue_id 逐项修订，返回每项的修订结果。

        Returns:
            {
              revised_content: str,
              fix_results: [{issue_id, original_content, revised_content,
                             change_summary, evidence_refs, status}],
              resolved_count: int,
              unresolved_count: int,
            }
        """
        if not content or not issues:
            return {
                "revised_content": content,
                "fix_results": [],
                "resolved_count": 0,
                "unresolved_count": 0,
            }

        ev_refs = [f"{e.get('source_id','')}:{e.get('source_title','')}"
                   for e in (evidence or [])[:3]]

        results = []
        current = content
        for iss in issues:
            iid = iss.get("issue_id", "unknown")
            desc = iss.get("description", iss.get("problem", ""))
            fix_hint = iss.get("suggested_fix", iss.get("fix", ""))
            severity = iss.get("severity", "minor")

            # 针对单个 issue 修正
            prompt = (
                f"只修正以下这一个问题，不要改动其他内容：\n\n"
                f"【问题ID】{iid}\n【严重程度】{severity}\n【问题描述】{desc}\n"
                f"【修改建议】{fix_hint}\n【参考证据】{', '.join(ev_refs) if ev_refs else '无'}\n\n"
                f"【当前内容】\n{current[:6000]}\n\n"
                f"输出修正后的完整内容，保留所有未被问题影响的部分不变。"
            )
            try:
                revised = await self._call_llm(prompt, temperature=0.3, max_tokens=2048)
                if revised and len(revised) > 50 and revised != current:
                    results.append({
                        "issue_id": iid,
                        "original_content": current[:200],
                        "revised_content": revised[:200],
                        "change_summary": f"Fixed [{severity}] {desc[:80]}",
                        "evidence_refs": ev_refs,
                        "status": "resolved",
                    })
                    current = revised
                else:
                    results.append({
                        "issue_id": iid,
                        "original_content": current[:200],
                        "revised_content": current[:200],
                        "change_summary": f"Unable to fix [{severity}] {desc[:80]}",
                        "evidence_refs": ev_refs,
                        "status": "unresolved",
                    })
            except Exception:
                results.append({
                    "issue_id": iid, "original_content": current[:200],
                    "revised_content": current[:200],
                    "change_summary": f"LLM error fixing {iid}",
                    "evidence_refs": ev_refs, "status": "unresolved",
                })

        resolved = sum(1 for r in results if r["status"] == "resolved")
        unresolved = len(results) - resolved
        return {
            "revised_content": current,
            "fix_results": results,
            "resolved_count": resolved,
            "unresolved_count": unresolved,
        }

    async def fix_batch(self, content: str, issues: list[dict],
                        evidence: list[dict] = None) -> dict:
        """批量修复 — 一次性把全部问题下发给 LLM,单次调用完成所有修订。

        与 fix_with_tracking(逐 issue 串行)返回同构结果,便于对比与复用:
        {revised_content, fix_results, resolved_count, unresolved_count}
        """
        if not content or not issues:
            return {
                "revised_content": content,
                "fix_results": [],
                "resolved_count": 0,
                "unresolved_count": 0,
            }

        ev_refs = [f"{e.get('source_id','')}:{e.get('source_title','')}"
                   for e in (evidence or [])[:3]]

        issues_text = "\n".join(
            f"{idx + 1}. [{i.get('severity', 'minor')}] [{i.get('issue_id', '?')}] "
            f"{i.get('location', '')}: {i.get('description', i.get('problem', ''))}\n"
            f"    建议: {i.get('suggested_fix', i.get('fix', ''))}"
            for idx, i in enumerate(issues)
        )

        prompt = (
            f"请一次性修正以下内容的全部 {len(issues)} 个审核问题,输出修正后的完整内容。\n\n"
            f"【参考证据】{', '.join(ev_refs) if ev_refs else '无'}\n\n"
            f"【审核问题(共 {len(issues)} 条)】\n{issues_text}\n\n"
            f"【当前内容】\n{content}\n\n"
            f"要求:逐条落实上述问题的修改建议;无法修改的问题保持原文;"
            f"直接输出修正后的完整 Markdown,不要输出 JSON、不要附加任何说明文字。"
        )

        revised = content
        status = "unresolved"
        try:
            out = await self._call_llm(prompt, temperature=0.3, max_tokens=8000)
            if out and len(out) > 50 and out != content:
                revised = out
                status = "resolved"
        except Exception:
            pass

        fix_results = [{
            "issue_id": i.get("issue_id", "unknown"),
            "original_content": content[:200],
            "revised_content": revised[:200],
            "change_summary": f"批量修复 [{i.get('severity', 'minor')}] "
                              f"{i.get('description', i.get('problem', ''))[:80]}",
            "evidence_refs": ev_refs,
            "status": status,
        } for i in issues]

        resolved = len(issues) if status == "resolved" else 0
        return {
            "revised_content": revised,
            "fix_results": fix_results,
            "resolved_count": resolved,
            "unresolved_count": len(issues) - resolved,
        }

    async def execute(self, state: dict) -> dict:
        doc = state.get("lecture_doc", {})
        content = doc.get("content", "")
        audit = state.get("audit_report", {})
        issues = audit.get("issues", []) if isinstance(audit, dict) else []
        evidence = state.get("knowledge_context", {}).get("sources", [])
        return await self.fix_batch(content, issues, evidence)


def get_fix_agent() -> FixAgent:
    return FixAgent()
