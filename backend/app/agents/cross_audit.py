"""CrossValidationAudit — 多角色交叉验证审核(消除幻觉的核心机制)。

3 个独立视角的审核官并行审核、交叉汇总:
  1. 事实核验官 —— 幻觉检测 / 知识依据 / 引用完整性 → 幻觉率
  2. 内容质量官 —— 准确性 / 完整性 / 代码正确性
  3. 难度匹配官 —— 内容难度 vs 学习者领域技能画像 → 难度匹配分

产出(与 AuditAgent 同构,可直接替换):
  overall_confidence(加权置信度)、hallucination_rate(幻觉率,<5% 达标)、
  difficulty_match_score(难度匹配分,≥75 达标)、按类别/审核官标注的 issues。
"""
import asyncio
import json
import re
import uuid
from typing import Any, Dict, List

from .base import BaseAgent

_JUDGES: List[Dict[str, Any]] = [
    {
        "name": "事实核验官",
        "weight": 0.4,
        "prompt": """你是"事实核验官"，职责是揪出 AI 生成内容里的"幻觉"。只从这 4 个角度审核（不要管难度、完整性）：
1. 知识依据：内容是否有知识库证据支撑
2. 无来源事实：是否出现知识库未支持的事实断言（幻觉）
3. 事实冲突：内容是否与知识库证据矛盾
4. 引用完整性：是否遗漏必要的知识来源引用

输出 JSON（不要加任何解释）：
{"overall_confidence": 0到100的整数, "issues": [{"severity":"critical|major|minor","description":"问题描述","suggested_fix":"修改建议","category":"hallucination|citation"}], "hallucination_rate": 0到100的整数（估计内容中幻觉/无依据内容的占比，<5为达标）}""",
    },
    {
        "name": "内容质量官",
        "weight": 0.4,
        "prompt": """你是"内容质量官"，职责是确保内容专业、完整、可运行。只从这 3 个角度审核：
1. 准确性：概念、定义、API 是否准确
2. 完整性：核心知识点是否覆盖
3. 代码正确性：Python 代码是否有明显错误

输出 JSON：
{"overall_confidence": 0到100的整数, "issues": [{"severity":"critical|major|minor","description":"问题描述","suggested_fix":"修改建议","category":"accuracy|completeness|code"}]}""",
    },
    {
        "name": "难度匹配官",
        "weight": 0.2,
        "prompt": """你是"难度匹配官"，职责是判断内容难度是否贴合学习者水平。根据给定的学习者领域技能分数(0-100)：分数低(<35)应给基础讲解、多用类比；分数高(>70)应给进阶、深入原理。输出 difficulty_match_score(0-100，100=完美匹配，<75=不匹配)。

输出 JSON：
{"overall_confidence": 0到100的整数, "issues": [{"severity":"critical|major|minor","description":"问题描述","suggested_fix":"修改建议","category":"difficulty"}], "difficulty_match_score": 0到100的整数}""",
    },
]

_DEBATE_ARBITER_PROMPT = """你是"辩论仲裁官"。多位审核官对同一份内容提出了问题,但其中可能存在误报。你的职责是逐条仲裁,判断每个问题是「真问题(confirmed)」还是「误报(refuted)」。

仲裁原则:
- 对照知识库证据:若内容确实缺乏证据支撑、与证据矛盾、或明显错误 → confirmed
- 若问题描述与实际内容不符、或内容其实有依据、或问题过于宽泛无实质 → refuted

输出 JSON(只输出仲裁结果):
{"verdicts": [{"issue_id":"...","verdict":"confirmed|refuted","reason":"20字内理由"}]}"""


class CrossValidationAudit(BaseAgent):
    """多角色交叉验证审核 Agent —— 3 审核官独立审、交叉汇总。"""

    def __init__(self):
        super().__init__("CrossValidationAudit", "多角色交叉验证审核")
        self._judges = _JUDGES

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        items = self._extract_items(state)
        profile = state.get("profile", {})
        domain_context = state.get("domain_context", {})
        evidence = state.get("knowledge_context", {}).get("sources", [])
        ev_refs = self._format_evidence(evidence)

        # 3 个审核官并行审核
        results = await asyncio.gather(
            *[self._run_judge(j, items, domain_context, ev_refs) for j in self._judges],
            return_exceptions=True,
        )

        all_issues: List[dict] = []
        confidences: List[int] = []
        available_weights: List[float] = []
        judges_summary: Dict[str, Any] = {}
        hallucination_rate = None
        difficulty_match_score = None

        for judge, result in zip(self._judges, results):
            name = judge["name"]
            if isinstance(result, Exception):
                judges_summary[name] = {"confidence": None, "issues": 0, "available": False, "error": str(result)[:80]}
                continue
            if not result.get("service_available", True):
                judges_summary[name] = {"confidence": None, "issues": 0, "available": False,
                                        "error": result.get("error", "audit service unavailable")[:80]}
                continue
            issues = result.get("issues", [])
            conf = int(result.get("overall_confidence", 50))
            confidences.append(conf)
            available_weights.append(judge["weight"])
            judges_summary[name] = {"confidence": conf, "issues": len(issues)}
            for iss in issues:
                iss.setdefault("issue_id", f"iss-{uuid.uuid4().hex[:8]}")
                iss.setdefault("category", "general")
                iss.setdefault("judge", name)
            all_issues.extend(issues)
            if "hallucination_rate" in result and result["hallucination_rate"] is not None:
                hallucination_rate = int(result["hallucination_rate"])
            if "difficulty_match_score" in result and result["difficulty_match_score"] is not None:
                difficulty_match_score = int(result["difficulty_match_score"])

        # 辩论仲裁:对高危/幻觉/引用类问题仲裁,剔除误报
        disputed = [i for i in all_issues if i.get("severity") in ("critical", "major")
                    or i.get("category") in ("hallucination", "citation")]
        debate = {"arbitrated_count": len(disputed), "confirmed_count": 0, "refuted_count": 0}
        if disputed:
            verdicts = await self._arbitrate(disputed, items, ev_refs)
            refuted_ids = {v.get("issue_id") for v in verdicts if v.get("verdict") == "refuted"}
            debate["refuted_count"] = len(refuted_ids)
            debate["confirmed_count"] = len(disputed) - len(refuted_ids)
            all_issues = [i for i in all_issues if i.get("issue_id") not in refuted_ids]

        # 加权置信度(事实核验 0.4 / 内容质量 0.4 / 难度匹配 0.2)
        overall = round(sum(c * w for c, w in zip(confidences, available_weights)) / sum(available_weights)) if confidences else 0

        # 幻觉率兜底:若事实核验官未给出,用"幻觉/引用类问题占全部问题比例"代理
        if hallucination_rate is None:
            hc = sum(1 for i in all_issues if i.get("category") in ("hallucination", "citation"))
            hallucination_rate = round(hc / max(1, len(all_issues)) * 100, 1)

        passed = overall >= 75
        self.log(
            f"交叉验证+辩论: {len(all_issues)} 问题"
            f"(仲裁{debate['arbitrated_count']}条,剔除误报{debate['refuted_count']}条), "
            f"置信度={overall}%, 幻觉率={hallucination_rate}%, 难度匹配={difficulty_match_score}"
        )

        return {
            "audit_report": {
                "overall_confidence": overall,
                "passed": passed,
                "total_issues": len(all_issues),
                "critical_issues": len([i for i in all_issues if i.get("severity") == "critical"]),
                "items_audited": len(items),
                "issues": all_issues,
                "hallucination_rate": hallucination_rate,
                "difficulty_match_score": difficulty_match_score,
                "judges": judges_summary,
                "debate": debate,
                "mode": "cross_validation + debate",
                "service_available": bool(confidences),
            },
            "audit_passed": passed,
        }

    # ================================================================
    # 内部方法
    # ================================================================
    async def _arbitrate(self, disputed: List[dict], items: list, ev_refs: list) -> List[dict]:
        """辩论仲裁:对争议问题逐条裁定 confirmed(真问题)/ refuted(误报)。"""
        content_text = "\n\n".join(item.get("content", "") for item in items)[:3000]
        issues_text = "\n".join(
            f"[{i.get('issue_id')}] ({i.get('judge')}/{i.get('category')}/{i.get('severity')}) "
            f"{i.get('description', '')[:100]}"
            for i in disputed[:15]
        )
        ev_str = "\n".join(f"- {r}" for r in ev_refs) if ev_refs else "无"
        user_prompt = (
            f"【内容】\n{content_text}\n\n"
            f"【待仲裁的问题】\n{issues_text}\n\n"
            f"【知识库证据】\n{ev_str}\n\n"
            f"请逐条仲裁,输出 JSON。"
        )
        try:
            messages = [
                {"role": "system", "content": _DEBATE_ARBITER_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            raw = await self.llm.chat(messages, temperature=0.2, max_tokens=1200)
            parsed = self._parse_json(raw)
            if parsed:
                return parsed.get("verdicts", [])
        except Exception:
            pass
        # 仲裁失败:默认全部保留(不误删)
        return [{"issue_id": i.get("issue_id"), "verdict": "confirmed", "reason": "仲裁失败默认保留"}
                for i in disputed]

    async def _run_judge(self, judge: dict, items: list, domain_context: dict,
                         ev_refs: list) -> dict:
        """单个审核官并行审核所有资源项,汇总该官结果。"""
        user_prompts = [self._build_user_prompt(judge["name"], item, domain_context, ev_refs) for item in items]
        raws = await asyncio.gather(
            *[self._call_judge(judge["prompt"], p) for p in user_prompts],
            return_exceptions=True,
        )

        all_issues: List[dict] = []
        confidences: List[int] = []
        meta: Dict[str, Any] = {}

        for raw in raws:
            if isinstance(raw, Exception):
                continue
            parsed = self._parse_json(raw)
            if not parsed:
                continue
            confidences.append(int(parsed.get("overall_confidence", 50)))
            all_issues.extend(parsed.get("issues", []))
            if "hallucination_rate" in parsed and parsed["hallucination_rate"] is not None:
                meta["hallucination_rate"] = int(parsed["hallucination_rate"])
            if "difficulty_match_score" in parsed and parsed["difficulty_match_score"] is not None:
                meta["difficulty_match_score"] = int(parsed["difficulty_match_score"])

        if not confidences:
            return {"service_available": False, "error": "all audit calls failed"}
        overall = round(sum(confidences) / len(confidences))
        return {
            "service_available": True,
            "overall_confidence": overall,
            "issues": all_issues,
            "hallucination_rate": meta.get("hallucination_rate"),
            "difficulty_match_score": meta.get("difficulty_match_score"),
        }

    async def _call_judge(self, judge_prompt: str, user_prompt: str) -> str:
        """用审核官专属 system prompt 调用 LLM。"""
        messages = [
            {"role": "system", "content": judge_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.llm.chat(messages, temperature=0.3, max_tokens=1200)

    def _build_user_prompt(self, judge_name: str, item: dict, domain_context: dict,
                           ev_refs: list) -> str:
        score = domain_context.get("score")
        dc_str = f"学习者领域技能分数: {score}/100" if score is not None else "未知"
        ev_str = "\n".join(f"- {r}" for r in ev_refs) if ev_refs else "无"
        return (
            f"请以「{judge_name}」的职责审核以下 {item['type']} 类型内容:\n\n"
            f"【内容】\n{item['content']}\n\n"
            f"【学习者画像】{dc_str}\n\n"
            f"【知识库证据】\n{ev_str}\n\n"
            f"按你的职责输出 JSON。"
        )

    def _extract_items(self, state: dict) -> list:
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

    def _format_evidence(self, evidence: list) -> list:
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
        return ev_refs

    def _parse_json(self, raw: str) -> dict | None:
        if not raw:
            return None
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            pass
        m = re.search(r'\{[\s\S]*"overall_confidence"[\s\S]*\}', raw)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None


def get_cross_audit() -> CrossValidationAudit:
    return CrossValidationAudit()
