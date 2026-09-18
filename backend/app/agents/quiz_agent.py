"""QuizAgent — 基于学习者画像 + 知识证据生成个性化分阶测试题。

每个学习者、每个考点都会生成不同的专属题组：
- 难度 / 题型侧重 / 题干例子 / 解析详略都匹配该学员画像；
- 专业知识引用知识库证据（RAG 检索）；
- 纯 LLM 出题，不再回退到静态题库。
"""
from __future__ import annotations
import json, re, uuid
from typing import List, Dict, Any, Optional
from ..core.llm import get_llm_client
from ..rag.engine import RAGEngine
from ..core.config import settings
from ..services.quiz_bank import normalize_topic

QUIZ_SYSTEM_PROMPT = """你是 LearnMate 个性化出题 Agent。基于《Python数据分析实战》课程，为**指定学习者**生成专属分阶测试题。

## 出题要求
1. 必须覆盖四层: 基础题(1-2道) + 理解题(1-2道) + 实操题(1道) + 进阶题(1道)
2. 题型混合: single_choice(基础/理解)、short_answer(理解)、debugging(实操)、comprehensive(进阶)；不要全部生成单选题，必须包含至少 1 道代码/排错题
3. 每道题附带: 正确答案、详细解析、评分规则、证据引用
4. **严格个性化**，根据「学习者画像」定制：
   - 难度匹配该学员在当前知识点的真实掌握度
   - 题干例子优先使用学员专业背景相关的场景与术语
   - 认知风格影响题型与呈现方式（如偏好实操→多出 debugging/comprehensive）
   - 学习节奏慢→解析更细致、分步骤；节奏快→解析更精炼
   - 针对薄弱项多出对应知识点的题
5. 专业知识必须来自「参考资料」，没有证据支撑的专业事实必须标记 need_verification=true
6. 代码题(debugging/comprehensive)必须包含可运行的参考答案

## 输出 JSON（只输出 JSON，不要多余文字）
```json
{
  "questions": [
    {
      "id": "q-<uuid>",
      "knowledge_point": "Pandas DataFrame",
      "difficulty": "basic",
      "type": "single_choice",
      "question": "...",
      "options": [{"text": "...", "correct": true}, {"text": "...", "correct": false}],
      "answer": "...",
      "explanation": "...",
      "scoring_rule": "...",
      "evidence_refs": ["lecture-09:Series与DataFrame基础"],
      "need_verification": false
    }
  ]
}
```"""


class QuizAgent:
    """出题 Agent — 画像个性化 + 证据引用 + 纯 LLM 出题"""

    def __init__(self):
        self.rag = RAGEngine(str(settings.kb_path))
        self.llm = None
        try:
            self.llm = get_llm_client()
        except Exception:
            pass

    def generate(self, topic: str, count: int = 5, difficulty: str = "adaptive",
                 profile: list[int] | None = None, diagnosis: dict = None,
                 evidence: list[dict] = None, domain_context: dict = None,
                 learner_profile: dict = None) -> dict:
        """
        生成个性化分阶测试题。

        Args:
            topic: 主题（知识点分类）
            count: 总题数 (默认5, 最大10)
            difficulty: 难度等级 或 "adaptive"
            profile: 6维分数列表 (兼容旧接口)
            diagnosis: LearnerProfileOutput (兼容旧接口)
            evidence: 知识库证据列表（缺省时自动 RAG 检索）
            domain_context: {subtopic, score, lecture, path_type} 等
            learner_profile: 完整学习者画像 dict（专业背景/六维/领域技能/偏好）

        Returns:
            {topic, difficulty, questions[], sources[], generated_by, empty}
        """
        count = max(1, min(count, 10))
        subtopic = (domain_context or {}).get('subtopic') if domain_context else None
        canonical_topic = normalize_topic(topic)
        prompt_topic = subtopic or topic

        # 难度：服从该账号在当前知识点的真实掌握度（画像分数优先）。
        level = self._resolve_level(difficulty, profile, diagnosis, domain_context)

        # 画像上下文（决定题型侧重 / 题干例子 / 解析详略，是"每人不同"的关键）
        profile_context = self._build_profile_context(
            learner_profile, diagnosis, profile, domain_context)

        # 证据：优先外部传入，否则按考点 RAG 检索课程真实内容。
        evidence = evidence or []
        if not evidence:
            evidence = self.rag.search_evidence(prompt_topic, top_k=4) or []
            if not evidence and canonical_topic and canonical_topic != prompt_topic:
                evidence = self.rag.search_evidence(canonical_topic, top_k=4) or []
        ev_refs = [f"{e.get('source_id','')}:{e.get('source_title','')}" for e in evidence[:5]]

        # 纯 LLM 出题（不再回退静态题库）。
        questions = self._generate_with_llm(
            prompt_topic, count, level, evidence, profile_context)

        return {
            "topic": canonical_topic or topic,
            "difficulty": level,
            "questions": questions,
            "sources": ev_refs,
            "generated_by": "llm",
            "empty": len(questions) == 0,
        }

    # ---------- 难度解析 ----------

    def _resolve_level(self, difficulty: str, profile: list[int] | None,
                       diagnosis: dict, domain_context: dict) -> str:
        if domain_context and domain_context.get("score") is not None:
            level = self._difficulty_from_score(domain_context["score"])
        elif diagnosis:
            level = self._difficulty_from_diagnosis(diagnosis)
        else:
            level = self._difficulty_legacy(difficulty, profile)
        # 路径只是倾向，最终难度服从该账号在当前知识点的真实掌握度。
        if domain_context and domain_context.get("path_type") in {"path_2", "path_3"}:
            score = int(domain_context.get("score") or 0)
            if score < 35:
                level = "basic"
            elif score < 70:
                level = "intermediate"
            else:
                level = "advanced"
        return level

    # ---------- 画像上下文 ----------

    def _build_profile_context(self, learner_profile: dict, diagnosis: dict,
                               profile: list[int] | None, domain_context: dict) -> str:
        """把学习者画像转成 LLM 可消费的中文摘要，用于个性化出题。"""
        parts: list[str] = []
        lp = learner_profile or {}

        if lp.get("major_background"):
            parts.append(f"专业背景：{lp['major_background']}")

        six = lp.get("six_dims") or {}
        if six:
            dims = "、".join(f"{k}{v}分" for k, v in six.items() if v)
            if dims:
                parts.append(f"六维能力：{dims}")

        skills = lp.get("domain_skills") or {}
        if skills:
            sk = "、".join(f"{k}{v}分" for k, v in skills.items() if v)
            if sk:
                parts.append(f"领域技能：{sk}")

        weak = lp.get("domain_weak_skills") or lp.get("weak_dimensions") or []
        strong = lp.get("domain_strong_skills") or lp.get("strong_dimensions") or []
        if weak:
            names = "、".join(str(n) for n, _ in weak[:3])
            parts.append(f"薄弱项：{names}")
        if strong:
            names = "、".join(str(n) for n, _ in strong[:3])
            parts.append(f"强项：{names}")

        if lp.get("cognitive_style"):
            parts.append(f"认知风格：{lp['cognitive_style']}")
        if lp.get("learning_pace"):
            parts.append(f"学习节奏：{lp['learning_pace']}")
        if lp.get("learning_motivation"):
            parts.append(f"学习动机：{lp['learning_motivation']}")

        # 兼容旧接口：无 learner_profile 时用 diagnosis / profile 兜底
        if not parts and diagnosis:
            overall = diagnosis.get("overall_score")
            if overall is not None:
                parts.append(f"综合掌握度：{overall}分")
        if not parts and profile:
            parts.append(f"六维能力(旧)：{profile}")

        if not parts:
            return "- 无画像信息，按中等水平通用出题"

        return "\n".join(f"- {p}" for p in parts)

    # ---------- LLM 出题 ----------

    def _generate_with_llm(self, topic: str, count: int, level: str,
                           evidence: list[dict], profile_context: str) -> list[dict]:
        """纯 LLM 个性化出题。"""
        diff_label = {"basic": "基础", "intermediate": "中级", "advanced": "进阶"}.get(level, "中级")

        ctx_parts = []
        for e in (evidence or [])[:4]:
            ctx_parts.append(
                f"- [{e.get('source_id','')}] {e.get('source_title','')}: {e.get('content', '')[:300]}")
        evidence_text = "\n".join(ctx_parts) if ctx_parts else (
            "（无参考资料，请基于 Python 数据分析通用知识出题，专业事实标记 need_verification=true）")

        user = (
            f"主题/考点：{topic}\n"
            f"难度档位：{level}（{diff_label}）\n"
            f"数量：{count} 道\n\n"
            f"## 学习者画像\n{profile_context}\n\n"
            f"## 参考资料\n{evidence_text}\n\n"
            f"请根据画像与参考资料生成个性化分阶题目 JSON。"
        )
        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ]
        try:
            # chat_sync 兼容 async 路由（内部用线程池跑）与同步上下文。
            resp = self.llm.chat_sync(messages, temperature=0.8, max_tokens=2500)
            raw_questions = self._parse_questions(resp, count)
            return [self._normalize_question(q) for q in raw_questions][:count]
        except Exception:
            return []

    def _normalize_question(self, q: dict) -> dict:
        """把 LLM 原始输出规整为前端 QuizQuestion 兼容格式。

        LLM 输出 options 为 [{text, correct}] 对象数组、题干字段为 question、
        解析字段为 explanation；前端期望 options 字符串数组 + answer 索引、
        题干字段 q、解析字段 explain。这里统一转换，兼容两种 options 形态。
        """
        options = q.get("options") or []
        answer = q.get("answer")

        out: dict = {
            "id": q.get("id") or f"q-{uuid.uuid4().hex[:8]}",
            "type": q.get("type", "single_choice"),
            "difficulty": q.get("difficulty", "basic"),
            "q": q.get("question") or q.get("q") or "",
            "explain": q.get("explanation") or q.get("explain") or "",
            "knowledge_point": q.get("knowledge_point", ""),
            "scoring_rule": q.get("scoring_rule") or "正确得2分，错误得0分",
            "evidence_refs": q.get("evidence_refs") or [],
            "need_verification": q.get("need_verification", False),
        }

        if options and isinstance(options[0], dict):
            # 对象数组 → 字符串数组 + 正确选项索引
            texts: list[str] = []
            correct_idx = None
            for i, opt in enumerate(options):
                text = (opt.get("text") if isinstance(opt, dict) else str(opt)) or ""
                texts.append(text)
                if isinstance(opt, dict) and opt.get("correct") and correct_idx is None:
                    correct_idx = i
            out["options"] = texts
            out["answer"] = correct_idx if correct_idx is not None else (answer if isinstance(answer, int) else None)
        elif options:
            out["options"] = [str(o) for o in options]
            out["answer"] = answer if isinstance(answer, int) else None
        else:
            # 无选项（简答/排错题）：参考答案文本放入 reference，前端展示 explain 作解析
            out["options"] = None
            if answer is not None and not isinstance(answer, int):
                out["answer"] = None
                out["reference"] = answer
            else:
                out["answer"] = answer

        return out

    def _parse_questions(self, text: str, count: int) -> list[dict]:
        m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if not m:
            m = re.search(r'\{[\s\S]*"questions"[\s\S]*\}', text)
        if m:
            try:
                data = json.loads(m.group(1) if m.lastindex and m.group(1) else m.group())
                return data.get("questions", data if isinstance(data, list) else [])
            except (json.JSONDecodeError, KeyError):
                pass
        # Fallback: try array
        m = re.search(r'\[[\s\S]*\{[\s\S]*"type"[\s\S]*\}[\s\S]*\]', text)
        if m:
            try:
                data = json.loads(m.group())
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                pass
        return []

    # ---------- 难度映射 ----------

    def _difficulty_from_score(self, score: int) -> str:
        """由领域技能画像分数映射难度档位(与 CodeAgent 阈值一致)。"""
        if score < 35:
            return "basic"
        elif score < 70:
            return "intermediate"
        return "advanced"

    def _difficulty_from_diagnosis(self, diagnosis: dict) -> str:
        scores = diagnosis.get("mastery_scores", {})
        vals = [v for v in scores.values() if v > 0]
        overall = diagnosis.get("overall_score", sum(vals) // max(len(vals), 1) if vals else 50)
        if overall < 35:
            return "basic"
        elif overall < 70:
            return "intermediate"
        else:
            return "advanced"

    def _difficulty_legacy(self, difficulty: str, profile: list[int] | None) -> str:
        if difficulty == "adaptive" and profile:
            scores = [s for s in profile if s > 0]
            avg = sum(scores) / len(scores) if scores else 0
            if avg >= 80:
                return "advanced"
            elif avg <= 50:
                return "basic"
            return "intermediate"
        return difficulty if difficulty != "adaptive" else "intermediate"


def get_quiz_agent() -> QuizAgent:
    return QuizAgent()
