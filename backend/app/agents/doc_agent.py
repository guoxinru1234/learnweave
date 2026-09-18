"""讲义文档生成 Agent。

职责：根据学生画像、学习模式、知识库上下文，生成个性化 Markdown/HTML 格式讲义。
替代 CourseAgent.generate_lecture_structured() 的讲义部分。
"""

from typing import Dict, Any

from .base import BaseAgent

DOC_SYSTEM_PROMPT = """你是一位资深课程讲师，专注于生成高质量、个性化的学习讲义。

讲义只负责"讲概念、讲原理、讲坑"，**不包含完整代码示例和练习题**——这两类由专门的 CodeAgent、QuizAgent 单独产出，讲义里不要重复。

讲义的风格要求：
- 内容严格基于提供的知识库参考内容，杜绝凭空编造
- 根据学习者的领域技能掌握度调整难度（零基础→多用生活类比、少用术语、讲细；精通→深入底层原理、少啰嗦、多实战）
- 使用 HTML 标签组织内容（<h3>, <p>, <ul>, <li>, <strong>, <code>, <blockquote>, <table>）

必须包含的章节（每章至少 2-3 段）：
1. 引言（为什么学这个？实际应用场景）
2. 核心概念（每个概念先给生活类比，再给技术定义，关键术语用 <code> 标出）
3. 工作原理（分步骤讲解，说明机制与原因）
4. 常见错误与排错（列出 3-5 个新手常犯错误及解决方案）
5. 重点总结（用表格或列表总结关键知识点）

格式要求：
- 内容总量不少于 3000 字
- 重点用 [Star]重点 标记
- 易混淆点用 [WARN]易混淆 标记
"""


class DocAgent(BaseAgent):
    """讲义生成 Agent —— 专注于单次主题的个性化讲义生成。"""

    def __init__(self):
        super().__init__("DocAgent", DOC_SYSTEM_PROMPT)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("lecture_topic", "")
        profile = state.get("profile", {})
        mode = state.get("mode", "study")
        context = state.get("knowledge_context", {})
        domain_context = state.get("domain_context", {})

        prompt = self._build_prompt(topic, profile, mode, context, domain_context)
        content = await self._call_llm(prompt, temperature=0.7, max_tokens=8000)

        self.log(f"讲义生成完成，{len(content)} 字符")
        return {"lecture_doc": {"title": topic, "content": content, "mode": mode}}

    def _build_prompt(self, topic: str, profile: dict, mode: str,
                      context: dict, domain_context: dict = None) -> str:
        """根据学生画像和模式构建针对性 prompt。"""
        mode_config = self._get_mode_config(mode)
        domain_context = domain_context or {}
        score = domain_context.get("score")
        level = domain_context.get("level")
        skill_domain = domain_context.get("skill_domain") or topic

        # 知识基础:优先由领域技能分数推导,回退 profile.foundation
        foundation = profile.get("foundation")
        if score is not None:
            foundation = "零基础" if score < 35 else ("有一定基础" if score < 70 else "精通")
        foundation = foundation or "中等"

        # 学习风格:前端传了就按,否则按 level 给默认
        style = profile.get("style")
        if not style:
            style = {"basic": "视觉型", "intermediate": "综合型", "advanced": "理论型"}.get(level, "综合型")
        weakness = profile.get("weakness", [])

        style_hint = {
            "视觉型": "多用结构化呈现、代码高亮、流程描述",
            "听觉型": "语言清晰有节奏，多用类比和故事化表达",
            "动手型": "多给可运行的代码示例和实践任务",
            "理论型": "深入原理，给出严谨的推导过程",
            "综合型": "平衡理论与实践，兼顾概念与代码",
        }.get(style, "平衡理论与实践")

        weakness_hint = ""
        if score is not None and score < 60:
            weakness_hint = (
                f"\n注意：学生在「{skill_domain}」技能域掌握度仅 {score} 分（薄弱），"
                f"需重点讲解、多用生活类比和案例、少跳步、降低门槛。"
            )
        elif weakness:
            weakness_hint = (
                f"\n注意：学生的薄弱点包括 {', '.join(weakness)}，"
                f"在讲义中需要重点讲解这些内容，用更多案例帮助理解。"
            )

        # 由领域技能水平推导的个性化讲解要求(直接进 prompt,驱动内容差异)
        level_hint = {
            "basic": "零基础：每个概念先用生活类比再给技术定义，少用术语，放慢节奏、多举例",
            "intermediate": "有一定基础：概念与原理并重，适当深入",
            "advanced": "精通：深入底层原理，少啰嗦，多实战案例，术语直接使用",
        }.get(level, "平衡概念与原理")

        # 知识库上下文
        # 统一字段标准：knowledge_context 结构为 {"sources": [...], "topic": ...}，
        # 每条 evidence 字段为 knowledge_id/skill_domain/source_lesson/content/...。
        # 遍历 sources 把真实知识正文 + 知识点标识拼进 prompt。
        context_text = ""
        if context:
            import re
            sources = context.get("sources", []) or []
            parts = []
            seen_domains = set()
            for src in sources[:5]:
                title = src.get("source_title") or src.get("title", "")
                kid = src.get("knowledge_id", "")
                domain = src.get("skill_domain", "")
                content_raw = src.get("content") or ""
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                if content_raw:
                    plain = re.sub(r'<[^>]+>', '', content_raw).strip()[:1500]
                    if plain:
                        label = f"[{domain}] {title} ({kid})" if domain and kid else title
                        parts.append(f"- {label} {plain}")
            if parts:
                domain_hint = f"目标技能域：{', '.join(seen_domains)}" if seen_domains else ""
                context_text = f"""
【知识库参考内容（来自权威讲义）】：
{domain_hint}
{chr(10).join(parts)}

请严格基于以上参考内容进行总结、重组和扩写，确保内容准确，杜绝幻觉。
关键事实、命令、API 和工作原理后必须用方括号标注对应知识编号，
例如 [PY-ENV-001]。文末增加“参考依据”章节，列出实际使用的知识编号与来源标题。
"""

        return f"""请根据以下要求生成一份完整的学习讲义。

{context_text}

【主题】：{topic}

【学生画像】：
- 专业：{profile.get('major', '未知')}
- 年级：{profile.get('grade', '未知')}
- 知识基础：{foundation}
- 学习风格：{style} → 呈现方式：{style_hint}
{weakness_hint}

{mode_config['prompt_suffix']}

【个性化要求】：{level_hint}

【额外要求】：
- 内容深度：{mode_config['depth']}
- 案例数量：{mode_config['examples']} 个

输出 HTML 格式的完整讲义（用 <h3>, <p>, <ul>, <li>, <strong>, <code> 标签组织）。"""
