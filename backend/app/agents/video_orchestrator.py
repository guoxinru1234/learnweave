"""
视频生成协调器（完整版）—— 多 Agent 协作生成教学视频。

赛题核心要求："多模态教学视频/动画"

三阶段流水线（带质量迭代）:
  1. PlannerAgent — 根据讲义生成 12-15 幕分镜脚本
  2. CoderAgent — 将分镜转为渲染指令
  3. CriticAgent — 质量评审（score < 7.0 则迭代重来，最多 3 轮）

渲染方案（降级链）:
  优先 → 讯飞虚拟人 (XFYunVideoAgent) 数字人讲解
  其次 → Manim 黑板动画 + TTS 配音
  兜底 → Pillow 静态帧 + TTS 配音

整合:
  - 讯飞星火 TTS（最佳音质）/ edge-tts / pyttsx3
  - Manim 教学动画嵌入
  - 学生画像自适应（难度、语速、深度）
"""

import os
import json
import time
import tempfile
import asyncio
from typing import Optional, Dict, Any

from .planner_agent import PlannerAgent
from .coder_agent import CoderAgent
from .critic_agent import CriticAgent


class VideoOrchestrator:
    """视频生成协调器 — Planner → Coder → Critic → Render 完整流水线。

    赛题亮点：
    - 多 Agent 协作（3个专业Agent + 可选数字人Agent）
    - 质量迭代改进（CriticAgent 评分反馈驱动重生成）
    - 多模态融合（数字人/Manim动画/TTS配音）
    - 画像自适应（根据学生水平调整难度和深度）
    """

    MAX_ITERATIONS = 3        # 最多迭代 3 轮
    QUALITY_THRESHOLD = 7.0   # 质量阈值

    def __init__(self):
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.critic = CriticAgent()
        self._xfyun_video_agent = None  # 懒加载

    # ==================== 公共 API ====================

    def generate_video(
        self,
        lecture_title: str,
        lecture_data: dict = None,
        key_concepts: list = None,
        difficulty: str = "medium",
        profile: dict = None,
        use_digital_human: bool = True,
        use_manim: bool = True,
    ) -> dict:
        """同步入口：生成教学视频的完整流程。

        Args:
            lecture_title: 讲次标题
            lecture_data: 讲义数据（含 content 字段）
            key_concepts: 核心知识点列表
            difficulty: 难度 (basic/medium/advanced)
            profile: 学生画像 dict（6维度分数）
            use_digital_human: 是否尝试讯飞数字人
            use_manim: 是否尝试嵌入 Manim 动画

        Returns:
            dict 包含:
            - video_path: 最终视频路径
            - script: 分镜脚本
            - render_instructions: 渲染指令
            - iterations: 迭代记录 [{iteration, score, feedback, passed}]
            - final_score: 最终质量评分
            - passed: 是否通过质检
            - method: 渲染方式 (xfyun_digital_human / manim_blackboard / pillow_fallback)
            - agent_logs: Agent 协作日志
        """
        if lecture_data is None:
            lecture_data = {
                "title": lecture_title,
                "content": {
                    "introduction": f"{lecture_title} 课程介绍",
                    "core_knowledge": {
                        "concept": "核心概念讲解",
                        "principles": "1. 基本原理\n2. 工作机制\n3. 应用场景",
                    },
                    "key_points": key_concepts or ["核心知识点1", "核心知识点2"],
                    "summary": "本讲总结",
                }
            }

        if key_concepts:
            lecture_data.setdefault("key_concepts", key_concepts)

        # 注入画像信息
        if profile:
            lecture_data["student_profile"] = profile

        agent_logs = []

        # =========== 阶段 1: PlannerAgent 生成分镜 ===========
        agent_logs.append({"agent": "PlannerAgent", "status": "running", "timestamp": time.time()})
        try:
            script = self.planner.generate_script(lecture_data, difficulty)
            scene_count = len(script.get("scenes", []))
            agent_logs.append({
                "agent": "PlannerAgent", "status": "success",
                "scenes": scene_count, "timestamp": time.time()
            })
        except Exception as e:
            agent_logs.append({
                "agent": "PlannerAgent", "status": "error",
                "error": str(e), "timestamp": time.time()
            })
            return self._error_response(f"分镜生成失败: {e}", agent_logs)

        # =========== 阶段 2: CoderAgent 生成渲染指令 ===========
        agent_logs.append({"agent": "CoderAgent", "status": "running", "timestamp": time.time()})
        try:
            render_instructions = self.coder.generate_render_instructions(script)
            agent_logs.append({
                "agent": "CoderAgent", "status": "success", "timestamp": time.time()
            })
        except Exception as e:
            agent_logs.append({
                "agent": "CoderAgent", "status": "error",
                "error": str(e), "timestamp": time.time()
            })
            render_instructions = self.coder.generate_render_instructions_fallback(script)

        # =========== 阶段 3: CriticAgent 质量评审（带迭代改进）===========
        iterations = []
        for i in range(self.MAX_ITERATIONS):
            agent_logs.append({
                "agent": "CriticAgent", "status": "running",
                "iteration": i + 1, "timestamp": time.time()
            })
            try:
                review = self.critic.review(render_instructions)
            except Exception as e:
                review = self.critic.review_fallback(render_instructions)

            score = review.get("score", 6.0)
            passed = review.get("pass", score >= self.QUALITY_THRESHOLD)
            feedback = review.get("feedback", [])

            iterations.append({
                "iteration": i + 1,
                "score": score,
                "feedback": feedback,
                "passed": passed,
                "timestamp": time.time(),
            })
            agent_logs.append({
                "agent": "CriticAgent", "status": "success",
                "iteration": i + 1, "score": score, "passed": passed,
                "timestamp": time.time(),
            })

            if passed or i == self.MAX_ITERATIONS - 1:
                break

            # 根据反馈改进渲染指令
            agent_logs.append({
                "agent": "CoderAgent", "status": "retry",
                "iteration": i + 1, "feedback": feedback, "timestamp": time.time()
            })
            feedback_text = "；".join(feedback)
            try:
                render_instructions = self.coder.generate_render_instructions(script, feedback_text)
            except Exception:
                pass

        final_score = iterations[-1]["score"] if iterations else 6.0
        final_passed = iterations[-1]["passed"] if iterations else False

        # =========== 阶段 4: 视频渲染 ===========
        video_path = None
        method = "none"

        # 方案 A: 讯飞数字人（比赛加分项）
        if use_digital_human:
            try:
                xf_result = self._render_digital_human(script)
                if xf_result:
                    video_path = xf_result
                    method = "xfyun_digital_human"
                    agent_logs.append({
                        "agent": "XFYunVideoAgent", "status": "success",
                        "method": method, "timestamp": time.time()
                    })
            except Exception as e:
                agent_logs.append({
                    "agent": "XFYunVideoAgent", "status": "degraded",
                    "error": str(e), "timestamp": time.time()
                })

        # 方案 B: 本地渲染（Pillow + TTS + 可选 Manim 动画）
        if not video_path:
            try:
                local_result = self._render_local(
                    render_instructions, script, use_manim=use_manim
                )
                if local_result:
                    video_path = local_result
                    method = "local_rendering"
                    agent_logs.append({
                        "agent": "LocalRenderer", "status": "success",
                        "method": method, "timestamp": time.time()
                    })
            except Exception as e:
                agent_logs.append({
                    "agent": "LocalRenderer", "status": "error",
                    "error": str(e), "timestamp": time.time()
                })

        # =========== 组装返回结果 ===========
        return {
            "video_path": video_path,
            "script": script,
            "render_instructions": render_instructions,
            "iterations": iterations,
            "final_score": final_score,
            "passed": final_passed,
            "method": method,
            "agent_logs": agent_logs,
            "scene_count": len(script.get("scenes", [])),
            "generated_at": time.time(),
        }

    # ==================== 异步入口（用于 FastAPI） ====================

    async def generate_video_async(
        self,
        lecture_title: str,
        lecture_data: dict = None,
        key_concepts: list = None,
        difficulty: str = "medium",
        profile: dict = None,
        use_digital_human: bool = True,
        use_manim: bool = True,
    ) -> dict:
        """异步版本：在线程池中运行同步流水线，避免阻塞事件循环。"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_video(
                lecture_title=lecture_title,
                lecture_data=lecture_data,
                key_concepts=key_concepts,
                difficulty=difficulty,
                profile=profile,
                use_digital_human=use_digital_human,
                use_manim=use_manim,
            )
        )

    # ==================== 渲染方案 ====================

    def _render_digital_human(self, script: dict) -> Optional[str]:
        """方案 A: 讯飞虚拟人数字人视频。"""
        try:
            if self._xfyun_video_agent is None:
                from .xfyun_video_agent import XFYunVideoAgent
                self._xfyun_video_agent = XFYunVideoAgent()

            if not self._xfyun_video_agent.is_available:
                return None

            # 转换为虚拟人兼容格式
            vm_script = self._adapt_for_digital_human(script)

            # 同步调用异步方法
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在运行的事件循环中，用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            self._xfyun_video_agent.generate_video(vm_script)
                        )
                        return future.result(timeout=300)
                else:
                    return asyncio.run(self._xfyun_video_agent.generate_video(vm_script))
            except RuntimeError:
                return asyncio.run(self._xfyun_video_agent.generate_video(vm_script))

        except Exception as e:
            print(f"[VideoOrch] 数字人渲染失败: {e}")
            return None

    def _render_local(
        self, render_instructions: dict, script: dict, use_manim: bool = True
    ) -> Optional[str]:
        """方案 B: 本地渲染 — Pillow 黑板 + TTS 配音 + 可选 Manim 动画。"""
        try:
            from ..services.tts_service import TTSService
            from ..core.video_renderer_audio import render_video_with_audio

            # 获取分镜场景
            scenes = render_instructions.get("scenes", [])
            if not scenes:
                scenes = script.get("scenes", [])
            if not scenes:
                print("[VideoOrch] 无分镜场景，无法渲染")
                return None

            # 确定输出路径
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)
            )))
            media_dir = os.path.join(base_dir, "media", "videos")
            os.makedirs(media_dir, exist_ok=True)

            title = script.get("title", "lecture").replace(" ", "_")
            output_path = os.path.join(media_dir, f"video_{title}_{int(time.time())}.mp4")

            # 格式化场景
            formatted_scenes = self._format_scenes_for_renderer(scenes)

            # TTS 配音
            tts = TTSService()
            audio_dir = tempfile.mkdtemp(prefix="video_orch_tts_")
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            tts.synthesize_scenes(formatted_scenes, audio_dir)
                        )
                        audio_segments = future.result(timeout=120)
                else:
                    audio_segments = asyncio.run(
                        tts.synthesize_scenes(formatted_scenes, audio_dir)
                    )
            except RuntimeError:
                audio_segments = asyncio.run(
                    tts.synthesize_scenes(formatted_scenes, audio_dir)
                )

            print(f"[VideoOrch] TTS 完成: {len(audio_segments)} 段配音")

            # Manim 动画路径（可选）
            manim_paths = []
            if use_manim:
                manim_dir = os.path.join(media_dir)
                for f in sorted(os.listdir(manim_dir)):
                    if f.startswith("manim_") and f.endswith(".mp4"):
                        manim_paths.append(os.path.join(manim_dir, f))
                if manim_paths:
                    print(f"[VideoOrch] 找到 {len(manim_paths)} 个 Manim 动画")

            # 渲染视频
            result = render_video_with_audio(
                formatted_scenes,
                audio_segments,
                output_path=output_path,
                manim_paths=manim_paths if manim_paths else None,
                use_manim=False,  # 已在 manim_paths 中指定
            )

            return result

        except Exception as e:
            import traceback
            print(f"[VideoOrch] 本地渲染失败: {e}")
            traceback.print_exc()
            return None

    # ==================== 工具方法 ====================

    def _adapt_for_digital_human(self, script: dict) -> dict:
        """将分镜脚本适配为讯飞虚拟人格式。"""
        scenes = script.get("scenes", [])
        adapted_scenes = []
        for s in scenes:
            voiceover = s.get("voiceover", s.get("text", ""))
            adapted_scenes.append({
                "scene_id": s.get("scene_id", len(adapted_scenes) + 1),
                "type": s.get("type", "explain"),
                "title": s.get("text", voiceover[:30]),
                "voiceover": voiceover,
                "duration": s.get("duration", 5),
            })
        return {"title": script.get("title", ""), "scenes": adapted_scenes}

    def _format_scenes_for_renderer(self, scenes: list) -> list:
        """格式化场景以适配本地视频渲染器。"""
        formatted = []
        for s in scenes:
            formatted.append({
                "scene_id": s.get("scene_id", len(formatted) + 1),
                "type": s.get("type", "explain"),
                "text": s.get("text", s.get("voiceover", "")),
                "voiceover": s.get("voiceover", s.get("text", "")),
                "duration": s.get("duration", 5),
                "emphasis": s.get("type") in ("key_point", "confusion_point"),
            })
        return formatted

    def _error_response(self, message: str, agent_logs: list) -> dict:
        return {
            "video_path": None,
            "script": {},
            "render_instructions": {},
            "iterations": [],
            "final_score": 0,
            "passed": False,
            "method": "error",
            "agent_logs": agent_logs,
            "error": message,
        }

    # ==================== 便捷方法 ====================

    def generate_demo_video(self) -> dict:
        """生成演示视频（用于快速测试）。"""
        return self.generate_video(
            lecture_title="Pandas DataFrame 核心原理与实战",
            key_concepts=["DataFrame 操作", "groupby 聚合", "数据透视表", "链式操作"],
            difficulty="medium",
            use_digital_human=True,
            use_manim=True,
        )


# ==================== 全局单例 ====================

_video_orchestrator: Optional[VideoOrchestrator] = None


def get_video_orchestrator() -> VideoOrchestrator:
    """获取全局 VideoOrchestrator 实例。"""
    global _video_orchestrator
    if _video_orchestrator is None:
        _video_orchestrator = VideoOrchestrator()
    return _video_orchestrator
