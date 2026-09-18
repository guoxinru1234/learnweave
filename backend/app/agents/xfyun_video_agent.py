"""
讯飞星火虚拟人视频合成 Agent

职责：将分镜脚本 → 调用星火虚拟人 API → 生成带数字人讲课视频。

如果 API 不可用（未配置密钥 / 网络不通），自动降级为本地 Pillow + ffmpeg 渲染。
"""

import os
import json
import time
import hashlib
import hmac
import base64
import urllib.request
import urllib.error
import ssl
from typing import Optional

# 降级方案依赖
import tempfile
from ..core.video_renderer_audio import render_video_with_audio
from ..services.tts_service import TTSService


class XFYunVideoAgent:
    """
    星火虚拟人视频合成 Agent。

    使用流程：
        agent = XFYunVideoAgent()
        result = agent.generate_video(script, output_path)

    如果 XFYUN_APP_ID / XFYUN_API_SECRET 未设置或 API 调用失败，
    自动降级为本地渲染方案（Pillow 黑板 + AI 教师动画 + pyttsx3 TTS）。
    """

    # 讯飞虚拟人 API 配置 (vms2d = Virtual Man Service 2D)
    XFYUN_VMS_HOST = "vms.cn-huadong-1.xf-yun.com"
    XFYUN_VMS_START_PATH = "/v1/private/vms2d_start"
    XFYUN_VMS_CTRL_PATH = "/v1/private/vms2d_ctrl"

    def __init__(self):
        # 优先使用虚拟人专用密钥，其次使用通用星火密钥
        self.app_id = os.getenv("XFYUN_VMS_APP_ID", "") or os.getenv("XFYUN_APP_ID", "")
        self.api_secret = os.getenv("XFYUN_VMS_API_SECRET", "") or os.getenv("XFYUN_API_SECRET", "")
        self.api_key = os.getenv("XFYUN_VMS_API_KEY", "") or os.getenv("XFYUN_API_KEY", "")
        self._available = bool(self.app_id and self.api_secret)

        if self._available:
            print(f"[XFYunVideoAgent] 虚拟人已配置, app_id={self.app_id[:8]}...")
        else:
            print("[XFYunVideoAgent] 未配置密钥，将使用本地渲染降级方案")

    @property
    def is_available(self) -> bool:
        return self._available

    # ==================== 主入口 ====================

    async def generate_video(self, script: dict, output_path: Optional[str] = None) -> str:
        """
        根据分镜脚本生成讲课视频。

        Args:
            script: 分镜脚本 dict，需包含 scenes 列表，每场景含 text / type / duration。
            output_path: 输出 mp4 路径，默认使用临时文件。

        Returns:
            生成视频的文件路径。
        """
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".mp4", prefix="xfyun_video_")
            os.close(fd)

        # 尝试调用讯飞虚拟人 API
        if self._available:
            try:
                return await self._generate_via_xfyun(script, output_path)
            except Exception as e:
                print(f"[XFYunVideoAgent] 星火 API 调用失败: {e}，降级为本地渲染")

        # 降级：本地渲染
        return await self._generate_via_local(script, output_path)

    # ==================== 讯飞 API 调用 ====================

    def _build_auth_headers(self, host: str, path: str, method: str = "POST") -> dict:
        """构建讯飞 HMAC-SHA256 签名认证头。"""
        now = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        signature_origin = f"host: {host}\ndate: {now}\n{method} {path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode("ascii")
        authorization = (
            f'api_key="{self.api_key or self.app_id}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature}"'
        )
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Host": host,
            "Date": now,
            "Authorization": authorization,
        }

    def _call_vms_api(self, host: str, path: str, payload: dict) -> dict:
        """调用讯飞虚拟人 API。"""
        url = f"https://{host}{path}"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = self._build_auth_headers(host, path)
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"虚拟人 API HTTP {e.code}: {error_body[:500]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"虚拟人 API 网络错误: {e.reason}")

    async def _generate_via_xfyun(self, script: dict, output_path: str) -> str:
        """通过星火虚拟人 API 生成视频。"""
        import asyncio
        full_text = self._extract_full_script(script)

        # Step 1: 启动虚拟人会话
        start_payload = {
            "header": {"app_id": self.app_id},
            "parameter": {
                "vmr": {
                    "avatar_id": "110017006",  # 默认2D女教师形象
                    "width": 1280, "height": 720,
                    "stream": {"protocol": "rtmp"},
                }
            },
        }
        loop = asyncio.get_event_loop()
        print("[XFYunVideoAgent] 启动虚拟人会话...")
        start_resp = await loop.run_in_executor(
            None,
            lambda: self._call_vms_api(
                self.XFYUN_VMS_HOST, self.XFYUN_VMS_START_PATH, start_payload
            )
        )
        print(f"[XFYunVideoAgent] 会话启动: {json.dumps(start_resp, ensure_ascii=False)[:300]}")

        # 提取 session（控制请求必须携带，字段名是 "session" 不是 "session_id"）
        session_id = start_resp.get("header", {}).get("session", "")
        if not session_id:
            # 兼容旧版：尝试从 payload.vmr 中获取
            vmr = start_resp.get("payload", {}).get("vmr", {})
            session_id = vmr.get("session_id", vmr.get("session", ""))
        if not session_id:
            print("[XFYunVideoAgent] 警告: 未获取到 session，尝试不带 session 发送控制请求")
            print(f"[XFYunVideoAgent] 启动响应完整内容: {json.dumps(start_resp, ensure_ascii=False)[:500]}")

        # Step 2: 发送文本驱动虚拟人说话（必须携带 session）
        ctrl_payload = {
            "header": {
                "app_id": self.app_id,
                "session": session_id,  # 控制请求必填，字段名是 "session"
            } if session_id else {"app_id": self.app_id},
            "parameter": {"tts": {"vcn": "x5_lingxiaoxue", "speed": 50, "volume": 50}},
            "payload": {"text": {"encoding": "utf8", "text": base64.b64encode(full_text.encode("utf-8")).decode("ascii")}},
        }
        print("[XFYunVideoAgent] 发送文本驱动...")
        ctrl_resp = await loop.run_in_executor(
            None,
            lambda: self._call_vms_api(
                self.XFYUN_VMS_HOST, self.XFYUN_VMS_CTRL_PATH, ctrl_payload
            )
        )
        print(f"[XFYunVideoAgent] 驱动响应: {json.dumps(ctrl_resp, ensure_ascii=False)[:300]}")

        # Step 3: 获取视频 URL
        video_url = (
            ctrl_resp.get("payload", {}).get("video_url", "")
            or ctrl_resp.get("header", {}).get("video_url", "")
            or ctrl_resp.get("header", {}).get("stream_url", "")
        )
        if not video_url:
            # 从启动响应中获取 stream_url
            video_url = start_resp.get("header", {}).get("stream_url", "")
            if not video_url:
                vmr = start_resp.get("payload", {}).get("vmr", {})
                video_url = vmr.get("stream_url", "")

        if video_url:
            self._download_video(video_url, output_path)
            print(f"[XFYunVideoAgent] 星火虚拟人视频已生成: {output_path}")
            return output_path

        raise RuntimeError("虚拟人 API 未返回视频 URL，响应: " + json.dumps(ctrl_resp, ensure_ascii=False)[:500])

    # _call_xfyun_api 已删除，使用 _call_vms_api 替代

    # ==================== 本地渲染降级方案 ====================

    async def _generate_via_local(self, script: dict, output_path: str) -> str:
        """
        本地渲染降级方案：
        1. TTSService 为每个分镜合成 WAV 配音
        2. video_renderer_audio 合成最终视频（含 AI 教师动画 + 配音）
        """
        print("[XFYunVideoAgent] 启用本地降级渲染（Pillow + TTS + ffmpeg）")

        scenes = script.get("scenes", [])
        if not scenes:
            raise ValueError("分镜脚本 scenes 为空")

        # 格式化场景以适配本地渲染器
        formatted_scenes = []
        for s in scenes:
            formatted_scenes.append({
                "scene_id": s.get("scene_id", s.get("slide", 0)),
                "type": s.get("type", "explain"),
                "text": s.get("text", s.get("voiceover", s.get("title", ""))),
                "duration": s.get("duration", 5),
                "emphasis": s.get("type") in ("key_point", "confusion_point"),
            })

        # TTS 配音（async）
        tts = TTSService()
        audio_dir = tempfile.mkdtemp(prefix="xfyun_tts_")
        audio_segments = await tts.synthesize_scenes(formatted_scenes, audio_dir)

        # 渲染视频 + 配音混流（在线程池中运行同步函数）
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: render_video_with_audio(formatted_scenes, audio_segments, output_path=output_path)
        )

        print(f"[XFYunVideoAgent] 本地降级视频已生成: {result}")
        return result

    # ==================== 工具方法 ====================

    def _extract_full_script(self, script: dict) -> str:
        """
        从分镜脚本中提取完整的配音文本。
        优先使用 voiceover 字段，其次 title + bullets 组合。
        """
        scenes = script.get("scenes", [])
        texts = []
        for s in scenes:
            voiceover = s.get("voiceover", "")
            if voiceover:
                texts.append(voiceover)
            else:
                title = s.get("title", "")
                bullets = s.get("bullets", [])
                part = title
                if bullets:
                    part += "。" + "；".join(bullets)
                texts.append(part)
        return "\n".join(texts)

    def _download_video(self, url: str, output_path: str):
        """从 URL 下载视频文件。"""
        print(f"[XFYunVideoAgent] 下载视频: {url[:80]}...")
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "LearnWeave/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=300, context=ctx) as resp:
                with open(output_path, "wb") as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            print(f"[XFYunVideoAgent] 下载完成: {os.path.getsize(output_path)} bytes")
        except Exception as e:
            raise RuntimeError(f"下载视频失败: {e}")
