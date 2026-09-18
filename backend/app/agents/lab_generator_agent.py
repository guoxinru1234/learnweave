# backend/app/agents/lab_generator_agent.py
import json
from ..core.llm import get_llm_client


class LabGeneratorAgent:
    """实验题目生成智能体：根据讲次知识点自动生成实验任务"""

    def __init__(self):
        print("[INFO] LabGeneratorAgent 初始化 (统一 LLMClient)...")
        self.llm = get_llm_client()

    def _call_llm(self, prompt: str, max_tokens: int = 3000) -> str:
        """同步调用 LLM（底层 LLMClient 自带 3 次重试）"""
        return self.llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=max_tokens,
        )

    def generate_lab(self, lecture_topic: str, key_concepts: list, difficulty: str = "medium") -> dict:
        """
        根据讲次主题和关键概念生成实验题目
        """
        prompt = f"""
你是一位资深的Python数据分析实验设计专家。请根据以下讲次内容，设计一套完整的实验题目。

讲次主题：{lecture_topic}
关键概念：{', '.join(key_concepts)}
难度级别：{difficulty}（medium 表示中等难度）

请设计一份包含以下结构的实验题目，以 JSON 格式输出：

{{
    "title": "实验标题（简洁有力）",
    "purpose": ["实验目的1", "实验目的2", "实验目的3"],
    "environment": "实验环境描述（Python版本、核心库等）",
    "tasks": [
        {{
            "id": 1,
            "title": "任务一标题",
            "description": "详细任务描述",
            "score": "分值（如30分）",
            "requirements": ["要求1", "要求2"],
            "expected_output": "预期输出示例",
            "code_hint": "代码提示或框架（可选）"
        }},
        {{
            "id": 2,
            "title": "任务二标题",
            "description": "详细任务描述",
            "score": "分值",
            "requirements": ["要求1", "要求2"],
            "expected_output": "预期输出示例",
            "code_hint": "代码提示"
        }},
        {{
            "id": 3,
            "title": "任务三标题",
            "description": "详细任务描述",
            "score": "分值",
            "requirements": ["要求1", "要求2"],
            "expected_output": "预期输出示例",
            "code_hint": "代码提示"
        }}
    ],
    "code_framework": "基础代码框架（Python代码，包含必要的import语句）",
    "quiz": [
        {{"question": "思考题1", "answer_hint": "提示方向"}},
        {{"question": "思考题2", "answer_hint": "提示方向"}}
    ],
    "grading_criteria": {{
        "任务一": "评分标准描述",
        "任务二": "评分标准描述",
        "任务三": "评分标准描述"
    }}
}}

注意：任务要具体、可操作，要求清晰，预期输出要明确。
对于数据分析实验，可以包括Pandas数据清洗、groupby聚合、matplotlib可视化、NumPy运算等操作。
请确保实验任务合理、难度适中，适合学生独立完成。

只输出 JSON，不要有其他文字。
"""
        try:
            content = self._call_llm(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"生成实验题目失败: {e}")
            return self._generate_fallback_lab(lecture_topic, key_concepts)

    def _generate_fallback_lab(self, lecture_topic: str, key_concepts: list) -> dict:
        """备选方案：生成通用实验模板"""
        return {
            "title": f"{lecture_topic} 实验",
            "purpose": [
                f"掌握 {lecture_topic} 的核心概念",
                f"熟练运用 {', '.join(key_concepts[:2])} 进行数据处理"
            ],
            "environment": "Python 3.10+ / NumPy / Pandas / Matplotlib",
            "tasks": [
                {
                    "id": 1,
                    "title": "基础操作",
                    "description": f"使用Pandas读取数据并进行基本的数据探索和分析，包括 {', '.join(key_concepts[:3])}。",
                    "score": "30分",
                    "requirements": ["读取CSV数据", "使用head/info/describe探索数据", "检查缺失值和数据类型"],
                    "expected_output": "显示处理后的数据结果",
                    "code_hint": "df = pd.read_csv('data.csv'); print(df.head())"
                }
            ],
            "code_framework": "import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n\ndf = pd.read_csv('data.csv')\nprint(df.head())\nprint(df.describe())",
            "quiz": [
                {"question": "Pandas中链式操作的优势和注意事项", "answer_hint": "结合数据清洗的实际流程说明"}
            ],
            "grading_criteria": {"任务一": "代码正确，输出符合预期"}
        }


def get_lab_generator() -> LabGeneratorAgent:
    return LabGeneratorAgent()