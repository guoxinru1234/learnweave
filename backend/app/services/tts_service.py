"""TTS 配音服务 — 多层降级策略

策略优先级:
  1. 讯飞星火 TTS (长文本REST API, 音质极佳, 比赛推荐, 不需要额外开通)
  2. edge-tts (Microsoft Edge TTS, 国内被墙)
  3. pyttsx3 (Windows SAPI5, 离线兜底)
  4. 静音 WAV (极端情况保底)
"""
import os
import asyncio
import tempfile
import struct
import wave
import json
import time
import hashlib
import hmac
import base64
import urllib.request
import urllib.error
import ssl
from typing import Optional


class TTSService:
    """多层降级 TTS 配音服务。"""

    # 讯飞长文本 TTS API 配置
    XFYUN_TTS_HOST = "api-dx.xf-yun.com"
    XFYUN_TTS_CREATE_PATH = "/v1/private/dts_create"
    XFYUN_TTS_QUERY_PATH = "/v1/private/dts_query"

    def __init__(self):
        self._edge_available = None
        self._xfyun_tts_app_id = os.getenv("XFYUN_TTS_APP_ID", "") or os.getenv("XFYUN_APP_ID", "")
        self._xfyun_tts_api_key = os.getenv("XFYUN_TTS_API_KEY", "") or os.getenv("XFYUN_API_KEY", "")
        self._xfyun_tts_api_secret = os.getenv("XFYUN_TTS_API_SECRET", "") or os.getenv("XFYUN_API_SECRET", "")
        self._xfyun_tts_ok = bool(self._xfyun_tts_app_id and self._xfyun_tts_api_secret)

    # ==================== 讯飞 TTS (最佳音质) ====================

    def _xfyun_auth_headers(self, host: str, path: str, method: str = "POST") -> dict:
        """构建讯飞 HMAC-SHA256 签名认证头。"""
        now = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        sig_origin = f"host: {host}\ndate: {now}\n{method} {path} HTTP/1.1"
        sig = base64.b64encode(
            hmac.new(self._xfyun_tts_api_secret.encode(), sig_origin.encode(), hashlib.sha256).digest()
        ).decode()
        auth = (
            f'api_key="{self._xfyun_tts_api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{sig}"'
        )
        return {"Content-Type": "application/json", "Host": host, "Date": now, "Authorization": auth}

    def _xfyun_tts_create(self, text: str) -> str:
        """创建讯飞长文本 TTS 任务，返回 task_id。"""
        payload = {
            "header": {"app_id": self._xfyun_tts_app_id},
            "parameter": {
                "dts": {
                    "vcn": "x5_lingxiaoxue",  # 讯飞精品女声，教学场景
                    "speed": 50, "volume": 100, "pitch": 50,
                    "audio": {"encoding": "lame", "sample_rate": 16000},
                }
            },
            "payload": {"text": {"encoding": "utf8", "text": base64.b64encode(text.encode("utf-8")).decode("ascii")}},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = self._xfyun_auth_headers(self.XFYUN_TTS_HOST, self.XFYUN_TTS_CREATE_PATH)
        url = f"https://{self.XFYUN_TTS_HOST}{self.XFYUN_TTS_CREATE_PATH}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        # task_id is in header.task_id (not payload.dts)
        task_id = result.get("header", {}).get("task_id", "")
        if not task_id:
            # Fallback: try old payload.dts path
            task_id = result.get("payload", {}).get("dts", {}).get("task_id", "")
        if not task_id:
            raise RuntimeError(f"TTS任务创建失败: {json.dumps(result, ensure_ascii=False)[:300]}")
        return task_id

    def _xfyun_tts_query(self, task_id: str) -> str:
        """查询 TTS 任务，返回音频下载 URL。

        新版 API 格式：
        - task_id 放在 header 中
        - task_status 在 header 中（"5"=完成）
        - 音频数据在 payload.audio.audio (base64)
        """
        payload = {
            "header": {"app_id": self._xfyun_tts_app_id, "task_id": task_id},
            "parameter": {},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = self._xfyun_auth_headers(self.XFYUN_TTS_HOST, self.XFYUN_TTS_QUERY_PATH)
        url = f"https://{self.XFYUN_TTS_HOST}{self.XFYUN_TTS_QUERY_PATH}"
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        task_status = str(result.get("header", {}).get("task_status", ""))
        if task_status == "5":  # 完成
            # 新版 API: 音频在 payload.audio.audio (base64 编码的 URL)
            audio_b64 = result.get("payload", {}).get("audio", {}).get("audio", "")
            if audio_b64:
                audio_url = base64.b64decode(audio_b64).decode("utf-8")
                print(f"[TTS] 音频URL解码: {audio_url[:80]}...")
                return audio_url

            # 旧版兼容: payload.dts.audio_url
            audio_url = result.get("payload", {}).get("dts", {}).get("audio_url", "")
            if audio_url:
                return audio_url

        # 兼容旧版 status 字段
        old_status = result.get("payload", {}).get("dts", {}).get("status", -1)
        if old_status == 2:
            audio_url = result.get("payload", {}).get("dts", {}).get("audio_url", "")
            if audio_url:
                return audio_url

        raise RuntimeError(
            f"TTS任务未完成 task_status={task_status}: "
            f"{json.dumps(result, ensure_ascii=False)[:300]}"
        )

    async def _synthesize_xfyun(self, text: str, output_path: str) -> str | None:
        """使用讯飞星火 TTS API 合成语音。"""
        if not self._xfyun_tts_ok:
            return None
        try:
            loop = asyncio.get_event_loop()
            task_id = await loop.run_in_executor(None, self._xfyun_tts_create, text)
            # 轮询等待任务完成
            for _ in range(30):  # 最多等30秒
                await asyncio.sleep(1)
                try:
                    audio_url = await loop.run_in_executor(None, self._xfyun_tts_query, task_id)
                    # 下载音频（MP3 格式）
                    mp3_path = output_path.rsplit('.', 1)[0] + '.mp3'
                    def _download():
                        req = urllib.request.Request(audio_url)
                        ctx = ssl.create_default_context()
                        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
                            data = r.read()
                            print(f"[TTS] 下载音频: {len(data)} bytes")
                            with open(mp3_path, "wb") as f:
                                f.write(data)
                    await loop.run_in_executor(None, _download)
                    # 转 MP3 → WAV
                    if os.path.getsize(mp3_path) > 500:
                        import subprocess, shutil
                        # 查找 ffmpeg
                        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
                        # Windows 常见路径
                        for candidate in [
                            r"D:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
                            r"C:\ffmpeg\bin\ffmpeg.exe",
                            "ffmpeg",
                        ]:
                            if os.path.exists(candidate):
                                ffmpeg = candidate
                                break
                        subprocess.run(
                            [ffmpeg, "-y", "-i", mp3_path, "-acodec", "pcm_s16le",
                             "-ar", "44100", "-ac", "1", output_path],
                            capture_output=True, check=True, timeout=30
                        )
                        os.remove(mp3_path)
                        if os.path.getsize(output_path) > 500:
                            print(f"[TTS] 星火: {os.path.basename(output_path)} ({os.path.getsize(output_path)} bytes)")
                            return output_path
                except RuntimeError:
                    continue
            raise RuntimeError("TTS任务超时")
        except Exception as e:
            print(f"[TTS] 星火 TTS 失败: {e}")
            return None

    # ==================== edge-tts ====================

    async def _check_edge_tts(self) -> bool:
        if self._edge_available is not None:
            return self._edge_available
        try:
            import subprocess, sys
            result = subprocess.run(
                [sys.executable, "-c", "import edge_tts; print('ok')"],
                capture_output=True, text=True, timeout=10
            )
            self._edge_available = "ok" in result.stdout
        except Exception:
            self._edge_available = False
        return self._edge_available

    # ==================== 主入口 ====================

    async def synthesize(
        self, text: str, output_path: str = None, voice: str = "zh-CN-XiaoxiaoNeural"
    ) -> str:
        """将文本合成为 WAV 音频文件（多层降级）。"""
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="tts_")
            os.close(fd)
        if not output_path.endswith('.wav'):
            output_path = output_path.rsplit('.', 1)[0] + '.wav' if '.' in output_path else output_path + '.wav'

        if not text or not text.strip():
            return self._create_silent_wav(output_path, duration=1.0)

        # 策略 1: 讯飞星火 TTS (最佳音质，比赛加分)
        result = await self._synthesize_xfyun(text, output_path)
        if result:
            return result

        # 策略 2: edge-tts
        if await self._check_edge_tts():
            try:
                result = await self._synthesize_edge(text, output_path, voice)
                if result and os.path.getsize(result) > 500:
                    print(f"[TTS] edge-tts: {os.path.basename(output_path)} ({os.path.getsize(output_path)} bytes)")
                    return result
            except Exception as e:
                print(f"[TTS] edge-tts failed: {e}")

        # 策略 3: pyttsx3 (离线兜底)
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._worker_pyttsx3, text, output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                print(f"[TTS] pyttsx3: {os.path.basename(output_path)} ({os.path.getsize(output_path)} bytes)")
                return output_path
        except Exception as e:
            print(f"[TTS] pyttsx3 failed: {e}")

        # 策略 4: 静音兜底
        print(f"[TTS] All engines failed, using silent fallback")
        return self._create_silent_wav(output_path, duration=max(2.0, len(text) / 3.0))

    async def _synthesize_edge(self, text: str, output_path: str, voice: str) -> str:
        """使用 edge-tts 合成语音（异步）。"""
        import edge_tts
        # edge-tts 输出 MP3，需转为 WAV
        mp3_path = output_path.rsplit('.', 1)[0] + '.mp3'
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(mp3_path)

        # 用 ffmpeg 转 MP3→WAV（确保与合并逻辑兼容）
        import subprocess
        ffmpeg = r"D:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
        if not os.path.exists(ffmpeg):
            ffmpeg = "ffmpeg"

        subprocess.run(
            [ffmpeg, "-y", "-i", mp3_path, "-acodec", "pcm_s16le",
             "-ar", "44100", "-ac", "1", output_path],
            capture_output=True, check=True, timeout=30
        )
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return output_path

    def _worker_pyttsx3(self, text: str, output_path: str):
        """pyttsx3 合成（在 executor 线程中运行）。"""
        import pyttsx3
        engine = None
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                if "chinese" in v.name.lower() or "zh" in v.id.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 160)
            engine.setProperty("volume", 1.0)
            engine.save_to_file(text, output_path)
            engine.runAndWait()
        finally:
            if engine:
                try:
                    engine.stop()
                except Exception:
                    pass

    def _create_silent_wav(self, output_path: str, duration: float = 3.0) -> str:
        """创建静音 WAV（44100Hz 标准采样率）。"""
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        with wave.open(output_path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack('<h', 0) * n_samples)
        return output_path

    async def synthesize_scenes(
        self, scenes: list, output_dir: str = None
    ) -> list[dict]:
        """批量合成场景配音（限并发，避免 pyttsx3 崩溃）。"""
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="tts_scenes_")

        os.makedirs(output_dir, exist_ok=True)

        # 限制并发数（pyttsx3 不支持高并发，edge-tts 在国内被墙）
        sem = asyncio.Semaphore(2)

        async def _synth_one(i, scene):
            async with sem:
                voiceover = scene.get("voiceover", scene.get("text", ""))
                if not voiceover:
                    voiceover = scene.get("title", f"Scene {i+1}")
                audio_path = os.path.join(output_dir, f"scene_{i+1:02d}.wav")
                await self.synthesize(voiceover, output_path=audio_path)
                return i, audio_path, voiceover

        tasks = [_synth_one(i, s) for i, s in enumerate(scenes)]
        results_raw = await asyncio.gather(*tasks)

        results = []
        for i, audio_path, voiceover in results_raw:
            duration = max(2.0, len(voiceover) / 3.5)
            results.append({
                "scene_index": i,
                "audio_path": audio_path,
                "duration": duration,
                "text": voiceover,
            })

        print(f"[TTS] Batch complete: {len(results)} scenes -> {output_dir}")
        return results


_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service
