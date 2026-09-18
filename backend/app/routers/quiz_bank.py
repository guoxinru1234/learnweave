# backend/services/quiz_bank.py
import json
import asyncio
from typing import Optional, List, Dict
from ..core.llm import llm_client


async def _generate_questions_with_ai(topic: str, count: int = 5) -> List[Dict]:
    """调用 LLM 生成题目，返回题目列表"""
    prompt = f"""
你是一位 Python 数据分析教学专家。请生成 {count} 道关于「{topic}」的单选题，并附带答案解析。
要求：
- 覆盖该主题的核心概念、易混淆点和常见误区。
- 每道题提供 4 个选项（用 A、B、C、D 标识），并给出正确选项的字母。
- 解析应简明扼要，解释为什么正确/错误。
- 输出纯 JSON 数组，格式如下：
[
  {{"q": "题目文本", "options": ["A选项", "B选项", "C选项", "D选项"], "answer": "A", "explain": "解析文本"}}
]
不要输出其他任何内容。
"""
    try:
        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        # 提取 JSON（可能包含 Markdown 代码块）
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        questions = json.loads(response)
        # 标准化格式
        for q in questions:
            # 将 answer 从字母转为索引
            if isinstance(q.get("answer"), str) and q["answer"].upper() in "ABCD":
                q["answer"] = "ABCD".index(q["answer"].upper())
            # 确保 options 是列表
            if "options" in q and isinstance(q["options"], dict):
                q["options"] = list(q["options"].values())
            # 补充默认字段
            q.setdefault("explain", "解析：请结合课程内容理解。")
        return questions
    except json.JSONDecodeError as e:
        print(f"[QuizBank] JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"[QuizBank] AI 生成失败: {e}")
        return []


# 静态题库（作为降级方案，当 AI 不可用时使用）
FALLBACK_BANK = {
    "Python 基础": [
        {"q": "Python 中哪个数据类型是不可变序列？", "options": ["var", "val", "def", "let"], "answer": 1, "explain": "val 定义不可变引用。"},
        {"q": "Python 中 `df.describe()` 的作用是？", "options": ["输出前5行数据", "输出数值列的统计摘要（count/mean/std等）", "返回DataFrame的行数", "绘制直方图"], "answer": 1, "explain": "编译器可根据上下文自动推断类型。"},
    ],
    "高阶函数": [
        {"q": "map 和 flatMap 的主要区别是？", "options": ["map 转换后长度不变，flatMap 长度可变", "两者完全相同", "map 只能用于集合", "map 有副作用"], "answer": 0, "explain": "flatMap 先 map 再 flatten。"},
    ],
    # 其他知识点按需添加...
}


def recommendation_questions(topic: Optional[str] = None) -> List[Dict]:
    """
    入口函数：优先尝试 AI 生成，失败则降级到静态题库。
    注意：此函数是同步的，因为路由是同步的，内部使用 asyncio.run() 调用异步 AI 生成。
    """
    if not topic:
        topic = "Python 基础"

    try:
        # 尝试 AI 生成（同步包装）
        questions = asyncio.run(_generate_questions_with_ai(topic, count=5))
        if questions:
            return questions
    except Exception as e:
        print(f"[QuizBank] AI 生成失败，使用静态题库: {e}")

    # 降级到静态题库
    fallback = FALLBACK_BANK.get(topic, FALLBACK_BANK.get("Python 基础", []))
    # 返回前 5 道（如果不足，全部返回）
    return fallback[:5]