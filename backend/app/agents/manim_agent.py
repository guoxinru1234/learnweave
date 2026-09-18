"""Manim 动画 Agent — LLM 驱动，根据课程内容+学生画像动态生成教学动画

赛题核心要求："多模态教学视频/动画"
这是区别于幻灯片配音的真正 AI 生成动画。

支持多种 LLM 提供商（讯飞星火 / DeepSeek / OpenAI 等），通过 .env 统一配置。
"""

import json, os, re, tempfile
from typing import Dict, Any
from .base import BaseAgent
from ..core.config import settings

MANIM_SYSTEM_PROMPT = """你是 Manim 动画专家，为 Python数据分析课程生成教学动画代码。

## 关键要求：必须输出可运行的 Manim Python 代码，每个 self.play() 至少包含一个动画。

## 代码模板（严格遵循）：
```python
from manim import config
config.background_color = "#0f172a"
config.frame_width = 14
config.frame_height = 8
from manim import *

class ClassNameAnimation(Scene):
    def construct(self):
        # 1. 标题动画
        title = Text("中文标题", font_size=38, color="#818cf8")
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        self.wait(0.5)

        # 2. 核心概念 - 用带中文标签的矩形框展示
        box1 = Rectangle(width=5, height=1.5, color="#34d399", fill_opacity=0.2)
        box1.shift(UP*1)
        label1 = Text("中文概念标签", font_size=24, color="#e2e8f0")
        label1.move_to(box1)
        self.play(FadeIn(box1), Write(label1))
        self.wait(0.5)

        box2 = Rectangle(width=5, height=1.5, color="#f87171", fill_opacity=0.2)
        box2.shift(DOWN*1)
        label2 = Text("另一个中文标签", font_size=24, color="#e2e8f0")
        label2.move_to(box2)
        self.play(FadeIn(box2), Write(label2))
        self.wait(0.5)

        # 3. 箭头连接
        arrow = Arrow(box1.get_bottom(), box2.get_top(), color="#fbbf24")
        self.play(GrowArrow(arrow))
        self.wait(0.5)

        # 4. 总结提示
        tip = Text("中文总结文字", font_size=22, color="#fbbf24")
        tip.to_edge(DOWN, buff=0.4)
        self.play(Write(tip))
        self.wait(2)
```

## 规则
- 所有文本标签用中文。专业术语保留英文：NumPy, Pandas, DataFrame, GroupBy 等
- 颜色：P="#818cf8" A="#4f46e5" G="#34d399" Y="#fbbf24" R="#f87171" W="#e2e8f0"
- 每个 self.play() 必须包含至少一个动画：Write(), FadeIn(), GrowArrow(), Transform() 等
- 必须以 self.wait(2) 结束最后一个场景
- 画像适配：基础分<50 简化概念，基础分>80 加深内容
- 仅输出 Python 代码，不要任何解释文字"""


class ManimAgent(BaseAgent):
    """LLM 驱动的 Manim 动画生成 Agent。

    使用统一的 LLMClient（支持讯飞星火 / DeepSeek / OpenAI 等提供商），
    通过 .env 中的 LLM_PROVIDER 配置切换，无需修改代码。
    """

    def __init__(self):
        super().__init__("ManimAgent", MANIM_SYSTEM_PROMPT)
        self.log(f"使用 {settings.llm_provider.upper()} 生成 Manim 代码 (模型: {settings.llm_model})")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("lecture_topic", "Pandas")
        profile = state.get("profile", {})
        lecture_doc = state.get("lecture_doc", {})
        mode = state.get("mode", "study")

        # Extract content
        content = self._extract_content(lecture_doc, state.get("knowledge_context", {}))
        # Build profile-aware prompt
        prompt = self._build_prompt(topic, content, profile, mode)
        # Generate Manim script via LLM
        script = await self._generate_script(prompt)

        if not script:
            return {"manim_script": None, "manim_error": "LLM generation failed"}

        # Render via ManimService
        from ..services.manim_service import render_script

        # 绝对路径 — 输出到 backend/media/videos/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        media_dir = os.path.join(base_dir, "media", "videos")
        os.makedirs(media_dir, exist_ok=True)
        video_path = os.path.join(media_dir, f"manim_{self._safe_name(topic)}.mp4")

        success = await render_script(script, f"{self._safe_name(topic)}Animation", video_path)

        self.log(f"Manim animation: {video_path} {'OK' if success else 'FAILED'}")
        return {
            "manim_video": video_path if success else None,
            "manim_script": script,
            "generation_method": "llm_manim",
            "personalized_for": profile,
        }

    def _extract_content(self, lecture_doc: dict, context: dict) -> str:
        text = ""
        if lecture_doc.get("content"):
            text = re.sub(r'<[^>]+>', '', str(lecture_doc["content"]))
        elif context.get("sources"):
            texts = []
            for s in context["sources"][:3]:
                if isinstance(s, dict):
                    texts.append(s.get("content", s.get("text", "")))
                else:
                    texts.append(str(s))
            text = "\n".join(texts)
        return text[:2000]

    def _build_prompt(self, topic: str, content: str, profile: dict, mode: str) -> str:
        scores = []
        for k, v in profile.items():
            if isinstance(v, (int, float)) and v > 0:
                scores.append(f"{k}={v}")
        profile_str = ", ".join(scores) if scores else "no profile data"

        detail = "detailed" if mode in ("study", "challenge") else "concise"
        duration = {"preview": 30, "study": 60, "review": 45, "challenge": 90}.get(mode, 60)

        return f"""Generate a Manim animation ({duration}s, {detail}) for:

Topic: {topic}
Content: {content[:1500]}
Student profile: {profile_str}

Create a class named "{self._safe_name(topic)}Animation" with a construct() method.
Use boxed concepts, arrows for flow, color coding (G=correct, R=important, Y=highlight).
Keep text labels short. Include title, main concept visualization, and summary/wrap-up."""

    async def _generate_script(self, prompt: str) -> str | None:
        """生成并验证 Manim 脚本，最多重试 3 次。

        使用统一的 LLMClient（支持讯飞星火 / DeepSeek / OpenAI 等），
        通过 .env 中的 LLM_PROVIDER 配置切换提供商。
        """
        for attempt in range(3):
            try:
                raw = await self._call_llm(prompt, temperature=0.3, max_tokens=3000)

                # Extract code block
                if "```python" in raw:
                    code = raw.split("```python")[1].split("```")[0]
                elif "```" in raw:
                    code = raw.split("```")[1].split("```")[0]
                else:
                    code = raw

                code = code.strip()

                # Validate structure
                if not ("class " in code and "construct" in code and "from manim" in code):
                    self.log(f"第 {attempt+1} 次尝试：缺少 class/construct/import 结构，重试...")
                    prompt = f"{prompt}\n\n【严重警告】上一次输出缺少 class/construct/import。必须包含完整结构。"
                    continue

                # Validate has actual animation commands
                play_calls = re.findall(r'self\.play\(([^)]*)\)', code)
                has_content = any(call.strip() for call in play_calls)
                if not has_content:
                    self.log(f"第 {attempt+1} 次尝试：self.play() 为空，重试...")
                    prompt = f"{prompt}\n\n【严重警告】上一次 self.play() 参数为空。必须在 self.play() 内放入动画。"
                    continue

                if "self.wait(" not in code:
                    self.log(f"警告：缺少 self.wait()，但仍可使用")

                self.log(f"Manim 代码生成成功 ({len(code)} 字符, {len(play_calls)} 个动画调用)")
                return code

            except Exception as e:
                self.log(f"第 {attempt+1} 次 LLM 调用失败: {e}")
                if attempt == 2:
                    return None

        return None

    def _safe_name(self, topic: str) -> str:
        return re.sub(r'[^a-zA-Z0-9]', '_', topic)[:30]
