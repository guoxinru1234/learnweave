# backend/app/agents/coder_agent.py
"""视频渲染指令生成 Agent（配合视频生成流水线使用）"""
import json
from ..core.llm import get_llm_client


class CoderAgent:
    """程序员：将分镜脚本转换为渲染指令"""

    def __init__(self):
        self.llm = get_llm_client()

    def generate_render_instructions(self, script: dict, feedback: str = None) -> dict:
        """将分镜脚本转换为渲染指令"""
        prompt = f"""
你是一个视频生成程序员。请将以下分镜脚本转换为渲染指令。

脚本：
{json.dumps(script, ensure_ascii=False, indent=2)}

{f"用户反馈：{feedback}" if feedback else ""}

请输出 JSON 格式，每个 scene 包含：
- scene_id: 同脚本
- text: 画面文字（可优化排版）
- duration: 时长（秒）
- bg_color: 背景色
- text_color: 文字颜色（默认 white）

只输出 JSON，不要有其他文字。
"""
        content = self.llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000,
        )
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content)

    def generate_render_instructions_fallback(self, script: dict) -> dict:
        """备选渲染指令"""
        return {
            "scenes": script.get("scenes", [])
        }