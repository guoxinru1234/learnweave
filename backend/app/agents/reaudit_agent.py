"""ReAuditAgent — 对修订后内容重新验证，对比修订前后的变化。"""
from .audit_agent import AuditAgent


class ReAuditAgent:
    """复审 Agent — 重新审核修订后的内容，对比变化。

    输出:
      previous_score, current_score, resolved_issues, unresolved_issues,
      version, verified, retry_count
    """

    def __init__(self):
        self._audit = AuditAgent()

    async def reaudit(self, state: dict, previous_score: float,
                      fix_results: list[dict], version: int,
                      retry_count: int) -> dict:
        """对修订后内容重新验证。

        Args:
            state: 当前状态（含修订后的内容）
            previous_score: 上次审核的综合置信度
            fix_results: FixAgent.fix_with_tracking 返回的修订结果列表
            version: 当前版本号
            retry_count: 已重试次数

        Returns:
            {previous_score, current_score, resolved_issues, unresolved_issues,
             version, verified, retry_count}
        """
        result = await self._audit.execute(state)
        report = result.get("audit_report", {})
        current_score = report.get("overall_confidence", 0)

        resolved = [r for r in fix_results if r["status"] == "resolved"]
        unresolved = [r for r in fix_results if r["status"] == "unresolved"]

        # 如果还有 high severity 未解决，不能 verified=true
        has_critical_unresolved = any(
            r["status"] == "unresolved" for r in fix_results
        )

        verified = current_score >= 75 and not has_critical_unresolved

        return {
            "previous_score": previous_score,
            "current_score": current_score,
            "resolved_issues": resolved,
            "unresolved_issues": unresolved,
            "version": version,
            "verified": verified,
            "retry_count": retry_count + 1,
        }


def get_reaudit_agent() -> ReAuditAgent:
    return ReAuditAgent()
