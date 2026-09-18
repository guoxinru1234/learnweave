"""教学视频分镜生成 Agent（比赛要求新资源类型）。

职责：根据讲义内容生成 PPT 式教学视频的分镜脚本 + 触发实际视频渲染。
统一使用 PlannerAgent 生成渲染兼容的分镜格式，消除两套分镜逻辑。

流水线：
    讲义 → VideoAgent（教育脚本）→ PlannerAgent（渲染分镜）→ TTS + 视频渲染
"""

import json
import os
import re
import tempfile
from typing import Dict, Any

from .base import BaseAgent

VIDEO_SYSTEM_PROMPT = """你是一位教育视频制作专家。

你的职责是将讲义内容转化为教学视频的分镜脚本。
每页幻灯片包含：
- 标题（简洁有力）
- 2-4 个要点（bullet points）
- 配音文本（自然口语化，适合语音合成朗读）

设计原则：
- 控制每页信息量，一页一个核心概念
- 配音文本口语化，像老师在讲课而非念稿
- 重点页面做视觉标记（[Star]）
- 易混淆点用对比方式呈现
"""


class VideoAgent(BaseAgent):
    """视频分镜 Agent —— 生成幻灯片式教学视频分镜脚本并触发渲染。

    现在与 PlannerAgent + 渲染管道统一：
    1. LLM 生成教育分镜脚本（PPT 风格，含 voiceover）
    2. 调用 PlannerAgent 生成渲染兼容的分镜格式
    3. 异步触发视频渲染（TTS + Pillow 动画 + ffmpeg）
    """

    def __init__(self):
        super().__init__("VideoAgent", VIDEO_SYSTEM_PROMPT)
        self.seedance_available = False

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("lecture_topic", "")
        mode = state.get("mode", "study")
        lecture_doc = state.get("lecture_doc", {})
        context = state.get("knowledge_context", {})
        domain_context = state.get("domain_context", {})
        course_id = state.get("course_id", "")
        lecture_num = state.get("lecture_num", 0)

        # 1. 生成教育分镜脚本
        prompt = self._build_prompt(topic, mode, lecture_doc, context, domain_context)
        raw = await self._call_llm(prompt, temperature=0.5, max_tokens=2000)
        script = self._parse_script(raw)

        if not script:
            script = self._fallback_script(topic)

        slide_count = len(script.get("scenes", []))
        self.log(f"视频分镜生成完成，{slide_count} 页幻灯片")

        # 2. 转换为 PlannerAgent 渲染兼容格式 + 触发渲染
        render_scenes = self._convert_to_render_format(script)
        video_url = None

        try:
            video_url = await self._render_video(
                render_scenes, course_id, lecture_num
            )
            self.log(f"视频渲染完成: {video_url}")
        except Exception as e:
            self.log(f"视频渲染失败（分镜脚本已保存）: {e}")

        return {
            "video_script": {
                "title": topic,
                "scenes": script.get("scenes", []),
                "slide_count": slide_count,
                "generation_method": "llm_slideshow" if not self.seedance_available else "seedance",
                "mode": mode,
                "render_scenes": render_scenes,  # 渲染兼容格式
                "video_url": video_url,           # 已渲染的视频路径
            }
        }

    # ==================== 格式转换 ====================

    def _convert_to_render_format(self, script: dict) -> list:
        """
        将 VideoAgent 的 PPT 分镜格式转换为 PlannerAgent 的渲染格式。

        输入格式：
            {"slide": 1, "title": "...", "bullets": [...], "voiceover": "...", "type": "intro"}

        输出格式：
            {"scene_id": 1, "type": "intro", "text": "...", "duration": 5, "emphasis": false}
        """
        scenes = script.get("scenes", [])
        render_scenes = []

        for i, s in enumerate(scenes):
            scene_type = s.get("type", "explain")
            # voiceover 优先，其次 title + bullets
            text = s.get("voiceover", "")
            if not text:
                title = s.get("title", "")
                bullets = "；".join(s.get("bullets", []))
                text = f"{title}。{bullets}" if bullets else title

            # 根据文本长度估算时长（中文 ~3 字/秒）
            text_len = len(text)
            duration = max(3, min(8, text_len // 3))

            render_scenes.append({
                "scene_id": i + 1,
                "type": scene_type,
                "text": text[:80],  # 截断以适配画面
                "duration": duration,
                "emphasis": scene_type in ("key_point", "confusion_point"),
            })

        return render_scenes

    # ==================== 视频渲染 ====================

    async def _render_video(
        self, render_scenes: list, course_id: str, lecture_num: int
    ) -> str | None:
        """调用渲染管道生成实际视频文件（带超时保护，非阻塞）。"""
        import asyncio
        from ..services.tts_service import TTSService

        if not render_scenes:
            return None

        try:
            # 整个渲染流程最多 45 秒（为 orchestrator 的 60s 超时留余量）
            return await asyncio.wait_for(
                self._do_render(render_scenes, course_id, lecture_num),
                timeout=45.0,
            )
        except asyncio.TimeoutError:
            print(f"[VideoAgent] 视频渲染超时（>45s），跳过视频生成，分镜脚本已保留")
            return None
        except Exception as e:
            print(f"[VideoAgent] 视频渲染异常: {e}")
            return None

    async def _do_render(
        self, render_scenes: list, course_id: str, lecture_num: int
    ) -> str | None:
        """实际渲染逻辑（由 _render_video 带超时调用）。"""
        import asyncio
        from ..services.tts_service import TTSService
        from ..core.video_renderer_audio import render_video_with_audio

        # 确定输出路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        media_dir = os.path.join(base_dir, "media", "videos")
        os.makedirs(media_dir, exist_ok=True)
        output_path = os.path.join(media_dir, f"{course_id}_{lecture_num}.mp4")

        # TTS 配音 — 最多 30 秒，超时用静音兜底
        tts = TTSService()
        audio_dir = tempfile.mkdtemp(prefix="video_agent_tts_")
        try:
            audio_segments = await asyncio.wait_for(
                tts.synthesize_scenes(render_scenes, audio_dir),
                timeout=30.0,
            )
            print(f"[VideoAgent] TTS complete: {len(audio_segments)} audio segments")
        except asyncio.TimeoutError:
            print(f"[VideoAgent] TTS 超时，使用静音 WAV 兜底")
            # 为每个 scene 生成静音 WAV
            audio_segments = []
            for i, scene in enumerate(render_scenes):
                voiceover = scene.get("voiceover", scene.get("text", ""))
                silent_path = os.path.join(audio_dir, f"scene_{i+1:02d}.wav")
                tts._create_silent_wav(silent_path, duration=max(2.0, len(voiceover) / 3.5))
                audio_segments.append({
                    "scene_index": i,
                    "audio_path": silent_path,
                    "duration": max(2.0, len(voiceover) / 3.5),
                    "text": voiceover,
                })

        # 渲染视频 + 混流（在线程池中运行）
        def _render():
            return render_video_with_audio(
                render_scenes, audio_segments, output_path=output_path
            )

        result_path = await asyncio.to_thread(_render)

        # 返回前端可访问的相对路径
        return f"/media/videos/{course_id}_{lecture_num}.mp4"

    def _build_prompt(self, topic: str, mode: str, lecture_doc: dict,
                      context: dict, domain_context: dict = None) -> str:
        slide_count = {"preview": 3, "study": 6, "review": 8, "challenge": 10}
        target = slide_count.get(mode, 6)
        # 个性化:按领域技能掌握度微调页数(基础→少页,进阶→多页)
        level = (domain_context or {}).get("level")
        if level == "basic":
            target = max(3, target - 1)
        elif level == "advanced":
            target = min(12, target + 2)

        # 讲义内容或知识库内容
        content_text = ""
        if lecture_doc.get("content"):
            plain = re.sub(r'<[^>]+>', '', lecture_doc["content"])[:2000]
            content_text = f"讲义内容：{plain}"
        elif context.get("content"):
            plain = re.sub(r'<[^>]+>', '', context["content"])[:2000]
            content_text = f"知识点内容：{plain}"
        else:
            content_text = f"请根据 {topic} 的通用知识生成分镜。"

        return f"""根据以下内容，生成一个 {target} 页 PPT 式教学视频的分镜脚本。

{content_text}

每页 JSON 格式：
{{
  "scenes": [
    {{
      "slide": 1,
      "title": "幻灯片标题",
      "bullets": ["要点1", "要点2", "要点3"],
      "voiceover": "配音文本（口语化，50-80字）",
      "type": "intro/explain/key_point/confusion_point/summary"
    }}
  ]
}}

要求：
- slide 1：标题页（课程名 + 讲次名）
- slide 2：引入/学习目标
- slide 3-{target-1}：核心内容讲解
- slide {target}：总结回顾
- 重点内容标记 type: "key_point"
- 易混淆点标记 type: "confusion_point"
- 配音文本口语化，像老师在讲课

只输出 JSON，不要其他文字。"""

    def _parse_script(self, raw: str) -> dict | None:
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            return None

    def _fallback_script(self, topic: str) -> dict:
        return {
            "scenes": [
                {"slide": 1, "title": f"欢迎学习 {topic}", "bullets": ["课程概览", "学习目标"], "voiceover": f"大家好，今天我们来学习{topic}。", "type": "intro"},
                {"slide": 2, "title": "核心概念", "bullets": ["概念定义", "关键特征", "应用场景"], "voiceover": f"首先我们来理解{topic}的核心概念。", "type": "explain"},
                {"slide": 3, "title": "实践应用", "bullets": ["实战案例", "代码演示", "注意事项"], "voiceover": f"接下来我们看看{topic}的实际应用。", "type": "explain"},
                {"slide": 4, "title": "总结回顾", "bullets": ["核心要点", "下一步学习"], "voiceover": f"通过本节课的学习，我们掌握了{topic}的核心知识。", "type": "summary"},
            ],
        }
