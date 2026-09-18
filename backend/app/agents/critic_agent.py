# backend/app/agents/critic_agent.py
import json
from ..core.llm import get_llm_client


class CriticAgent:
    """鉴赏家：质检视频质量"""

    def __init__(self):
        print("[Look] CriticAgent 初始化 (统一 LLMClient)...")
        self.llm = get_llm_client()

    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """同步调用 LLM（底层 LLMClient 自带 3 次重试）"""
        return self.llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )

    def review(self, render_instructions: dict) -> dict:
        prompt = f"""
你是一个教育视频质检专家。请分析以下视频渲染指令，评估其教学效果。

渲染指令：
{json.dumps(render_instructions, ensure_ascii=False, indent=2)}

请从以下维度评分（满分10分）：
1. 内容结构（逻辑是否清晰，是否有渐进性）
2. 视觉设计（色彩搭配是否合理，文字是否易读）
3. 教学有效性（知识点是否准确传达）

输出 JSON：
{{
    "score": 8.5,
    "feedback": ["改进建议1", "改进建议2"],
    "pass": true
}}
"""
        try:
            content = self._call_llm(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"CriticAgent API 调用失败，使用备选方案: {e}")
            return self.review_fallback(render_instructions)

    def review_fallback(self, render_instructions: dict) -> dict:
        scenes = render_instructions.get("scenes", [])
        return {
            "score": 8.0 if len(scenes) >= 4 else 6.0,
            "feedback": ["画面数量合适" if len(scenes) >= 4 else "建议增加画面数量"],
            "pass": len(scenes) >= 4
        }