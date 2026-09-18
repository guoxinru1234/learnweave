"""CodeAgent — 生成结构化、可执行、可验证的个性化实操指南。"""
from __future__ import annotations
import asyncio, json, re, ast
from typing import Dict, Any, List
from .base import BaseAgent
from ..core.llm import get_llm_client

GUIDE_SYSTEM_PROMPT = """你是资深 Python 数据分析教育专家。根据学习者画像和知识库证据生成个性化实操指南。

输出 JSON，结构如下：
```json
{
  "title": "实操: Pandas DataFrame 基础操作",
  "objectives": ["学会创建 DataFrame", "掌握数据筛选"],
  "prerequisites": ["Python 基础语法", "已安装 pandas"],
  "difficulty": "intermediate",
  "steps": [
    {
      "step_number": 1,
      "instruction": "导入 pandas 并创建 DataFrame",
      "code": "import pandas as pd\\ndf = pd.DataFrame({'A':[1,2,3],'B':[4,5,6]})\\nprint(df)",
      "expected_result": "   A  B\\n0  1  4\\n1  2  5\\n2  3  6",
      "possible_errors": ["ModuleNotFoundError: 需 pip install pandas"],
      "verification_method": "运行代码，检查输出是否包含3行2列"
    }
  ],
  "code": "import pandas as pd\\n...",  // 完整可运行代码
  "expected_output": "...",
  "validation": "所有步骤通过 = 指南通过",
  "common_errors": ["缺少 pandas 库", "CSV 路径错误"],
  "hints": ["使用 df.head() 预览数据"],
  "evidence_refs": ["lecture-09:Series与DataFrame基础"]
}
```

要求:
- 代码必须与 topic 和 evidence 一致，使用 Pandas/NumPy/Matplotlib
- 根据 coding_ability: <35分→3步基础+详细注释, 35-70→5步+适度注释, >70→6步进阶+精简注释
- 不引用未在 evidence 中的库或 API"""


class CodeAgent(BaseAgent):
    """代码生成 Agent — 输出结构化实操指南"""

    def __init__(self):
        super().__init__("CodeAgent", GUIDE_SYSTEM_PROMPT)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """兼容编排器接口"""
        topic = state.get("lecture_topic", "")
        profile = state.get("profile", {})
        context = state.get("knowledge_context", {})
        evidence = context.get("sources", [])
        # 个性化:优先用领域技能画像分数,回退老六维 coding_ability
        domain_context = state.get("domain_context", {})
        coding_ability = domain_context.get("score")
        if coding_ability is None:
            coding_ability = profile.get("coding_ability", 50) if isinstance(profile, dict) else 50

        guide = await self.generate(topic=topic, coding_ability=coding_ability, evidence=evidence)
        return {"code_example": guide, "code_guide": guide}

    async def generate(self, topic: str, coding_ability: int = 50,
                       evidence: list[dict] = None) -> dict:
        """生成结构化实操指南。

        Returns:
            dict with title, objectives, prerequisites, difficulty, steps[],
                 code, expected_output, validation, common_errors, hints, evidence_refs
            On failure: {error, success: false}
        """
        evidence = evidence or []
        diff = "basic" if coding_ability < 35 else ("intermediate" if coding_ability < 70 else "advanced")
        steps_count = 3 if coding_ability < 35 else (5 if coding_ability < 70 else 6)
        annotate = "每行代码加中文注释解释" if coding_ability < 40 else ("关键行加注释" if coding_ability < 70 else "精简注释")

        ctx = "\n".join(
            f"- [{e.get('source_id','')}] {e.get('source_title','')}: {e.get('content','')[:300]}"
            for e in evidence[:3]
        ) if evidence else "无参考资料"

        prompt = (
            f"主题: {topic}\n"
            f"编程能力: {coding_ability}/100 ({diff})\n"
            f"步骤数: {steps_count}步, 注释要求: {annotate}\n"
            f"参考证据:\n{ctx}\n"
            f"请生成实操指南 JSON。"
        )

        try:
            resp = await self._call_llm(prompt, temperature=0.3, max_tokens=4000)
            guide = self._parse_guide(resp)
            if guide:
                # 语法检查
                code = guide.get("code", "")
                syntax_ok, syntax_err = self._check_syntax(code)
                guide["_syntax_check"] = {"passed": syntax_ok, "error": syntax_err}
                guide["_steps_count"] = len(guide.get("steps", []))
                guide["_coding_ability"] = coding_ability
                guide["difficulty"] = diff
                guide["success"] = True
                return guide
        except Exception:
            pass

        # 失败返回结构化错误
        return self._fallback_guide(topic)

    def _parse_guide(self, text: str) -> dict | None:
        m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
        if not m:
            m = re.search(r'\{[\s\S]*"title"[\s\S]*"steps"[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group(1) if m.lastindex and m.group(1) else m.group())
            except json.JSONDecodeError:
                pass
        return None

    def _check_syntax(self, code: str) -> tuple[bool, str]:
        if not code or not code.strip():
            return False, "Empty code"
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}"

    def _fallback_guide(self, topic: str) -> dict:
        return {
            "title": f"实操: {topic}",
            "objectives": [f"掌握 {topic} 的基本操作", f"理解 {topic} 的核心概念", f"能够独立编写 {topic} 代码"],
            "prerequisites": ["Python 3.8+", "pandas 已安装", "numpy 已安装"],
            "difficulty": "basic",
            "steps": [
                {"step_number": 1, "instruction": "导入必要的库", "code": "import pandas as pd\nimport numpy as np\nprint('Libraries loaded')",
                 "expected_result": "Libraries loaded", "possible_errors": ["ModuleNotFoundError: No module named 'pandas'"],
                 "verification_method": "检查无 ImportError"},
                {"step_number": 2, "instruction": "创建示例数据", "code": "df = pd.DataFrame({'name':['Alice','Bob'],'score':[85,92]})\nprint(df)",
                 "expected_result": "    name  score\n0  Alice     85\n1    Bob     92",
                 "possible_errors": ["NameError if pandas not imported"], "verification_method": "检查输出包含2行数据"},
                {"step_number": 3, "instruction": "数据分析操作", "code": "print(df.describe())\nprint(df['score'].mean())",
                 "expected_result": "统计摘要 + 平均值 88.5", "possible_errors": ["KeyError if column name wrong"],
                 "verification_method": "检查输出包含 count/mean/std 等统计量"},
            ],
            "code": "import pandas as pd\nimport numpy as np\ndf = pd.DataFrame({'name':['Alice','Bob'],'score':[85,92]})\nprint(df)\nprint(df.describe())\nprint(df['score'].mean())",
            "expected_output": "DataFrame + statistics + 88.5",
            "validation": "3 steps all pass = guide complete",
            "common_errors": ["pandas 未安装: pip install pandas", "numpy 未安装: pip install numpy"],
            "hints": ["使用 pip install pandas numpy 安装依赖"],
            "evidence_refs": [],
            "success": False,
            "error": "LLM generation failed, using deterministic fallback template with 3 steps",
        }


def get_code_agent() -> CodeAgent:
    return CodeAgent()
