"""视频 + 配音合成 — Python wave 合并 WAV + ffmpeg 混流"""
import os, shutil, tempfile, subprocess, wave, struct, math
import numpy as np
from moviepy.editor import VideoFileClip
from .video_renderer import render_video_from_scenes

_FFMPEG = r"D:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
if not os.path.exists(_FFMPEG):
    _FFMPEG = "ffmpeg"


def _make_beep(duration_ms=200, freq=880, sample_rate=44100):
    """生成一个短促的提示音 PCM 数据（用于验证音频是否工作）"""
    n = int(sample_rate * duration_ms / 1000)
    samples = []
    for i in range(n):
        t = i / sample_rate
        # 带衰减的 sine wave
        envelope = max(0, 1 - i / n)
        val = int(20000 * envelope * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', max(-32768, min(32767, val))))
    return b''.join(samples)


def render_video_with_audio(scenes, audio_segments, output_path=None, fps=24,
                             manim_paths: list = None, use_manim: bool = True):
    """合成最终视频：分镜 + 音频 + 可选 Manim 动画嵌入。

    黑板内容优先用 Manim 渲染（高质量动画排版），
    不可用时降级为 Pillow 静态帧。

    Args:
        scenes: 分镜列表
        audio_segments: TTS 配音片段
        output_path: 输出 mp4 路径
        manim_paths: 现有 Manim 视频路径列表，自动插入到合适位置
        use_manim: 是否尝试用 Manim 渲染黑板内容
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".mp4", prefix="video_")
        os.close(fd)
    if not scenes:
        raise ValueError("scenes empty")

    # 尝试用 Manim 渲染黑板内容
    manim_blackboard = None
    if use_manim:
        try:
            from .manim_renderer import render_manim_scenes
            manim_tmp = os.path.join(tempfile.gettempdir(), "_manim_blackboard.mp4")
            manim_blackboard = render_manim_scenes(scenes, manim_tmp, quality="low")
            if manim_blackboard:
                print(f"[AV] Manim 黑板渲染成功，使用 Manim 版画面")
        except Exception as e:
            print(f"[AV] Manim 黑板渲染失败: {e}")

    # 构建 Manim 额外剪辑列表
    extra_clips = []
    if manim_paths:
        positions = [max(1, len(scenes) * p // 10) for p in [3, 6]]
        for idx, mp in enumerate(manim_paths):
            if os.path.exists(mp) and os.path.getsize(mp) > 1000:
                try:
                    mc = VideoFileClip(mp).resize(width=1000)
                    pos = positions[idx % len(positions)]
                    extra_clips.append((mc, pos))
                    print(f"[AV] Manim 动画已加载: {os.path.basename(mp)} ({mc.duration:.1f}s) @ scene {pos}")
                except Exception as e:
                    print(f"[AV] Manim 加载失败: {mp} - {e}")

    if manim_blackboard and not extra_clips:
        # 纯 Manim 黑板 → 直接用作视频画面
        temp_video = manim_blackboard
        print(f"[AV] 使用纯 Manim 黑板视频")
    else:
        temp_video = os.path.join(tempfile.gettempdir(), "_temp_noaudio.mp4")
        if manim_blackboard:
            # Manim 黑板 + Manim 动画混合——暂时用 Pillow 合成，后续优化
            print(f"[AV] 混合模式: Manim黑板 + 动画片段")
        render_video_from_scenes(scenes, temp_video, extra_clips=extra_clips if extra_clips else None)

    # Collect valid WAVs
    wavs = []
    for s in audio_segments:
        ap = s.get("audio_path", "")
        if os.path.exists(ap) and os.path.getsize(ap) > 100:
            wavs.append(ap)

    if not wavs:
        print("[AV] No audio, copy only")
        shutil.copy2(temp_video, output_path)
        return output_path

    # Merge WAVs with Python wave, resample to 44100 Hz, add beep at start
    merged = os.path.join(tempfile.gettempdir(), "_merged.wav")
    TARGET_RATE = 44100  # Standard video-compatible sample rate

    try:
        # Read first WAV to get base format
        with wave.open(wavs[0], 'rb') as w0:
            src_rate = w0.getframerate()
            src_width = w0.getsampwidth()
            src_channels = w0.getnchannels()

        # Read all PCM data and concatenate
        all_frames = _make_beep(duration_ms=300, sample_rate=src_rate)  # 300ms beep at start
        for wf_path in wavs:
            with wave.open(wf_path, 'rb') as wi:
                all_frames += wi.readframes(wi.getnframes())

        # Resample if needed
        if src_rate != TARGET_RATE:
            import numpy as np
            raw = np.frombuffer(all_frames, dtype=np.int16)
            # Simple linear resampling
            ratio = TARGET_RATE / src_rate
            new_len = int(len(raw) * ratio)
            indices = np.clip((np.arange(new_len) / ratio).astype(int), 0, len(raw) - 1)
            raw = raw[indices]
            all_frames = raw.tobytes()

        # Write merged WAV at target rate
        with wave.open(merged, 'wb') as wo:
            wo.setnchannels(src_channels)
            wo.setsampwidth(src_width)
            wo.setframerate(TARGET_RATE)
            wo.writeframes(all_frames)

        print(f"[AV] Merged: {os.path.getsize(merged)} bytes, {len(wavs)} files @ {TARGET_RATE}Hz (beep added)")
    except Exception as e:
        print(f"[AV] WAV merge failed: {e}")
        import traceback
        traceback.print_exc()
        shutil.copy2(temp_video, output_path)
        return output_path

    # ffmpeg mux with explicit audio encoding settings
    try:
        subprocess.run([
            _FFMPEG, "-y",
            "-i", temp_video,
            "-i", merged,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",        # Explicit audio bitrate
            "-ar", str(TARGET_RATE),  # Ensure output sample rate
            "-ac", "1",             # Mono
            "-shortest",
            "-preset", "fast",
            "-crf", "23",
            output_path
        ], capture_output=True, check=True, timeout=120)
        print(f"[AV] Done: {output_path} ({os.path.getsize(output_path)} bytes)")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"[AV] ffmpeg error: {e.stderr[-300:].decode('utf-8', errors='replace') if e.stderr else 'unknown'}")
        shutil.copy2(temp_video, output_path)
        return output_path
    except Exception as e:
        print(f"[AV] mux failed: {e}")
        shutil.copy2(temp_video, output_path)
        return output_path


def create_teacher_badge_frame(width=160, height=120):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (width, height), (0,0,0,0))
    d = ImageDraw.Draw(img)
    cx, cy, r = width//2, height//2-10, 35
    d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(79,70,229,180), outline=(255,255,255,200), width=2)
    try:
        f = ImageFont.truetype("simhei.ttf", 14)
    except:
        f = ImageFont.load_default()
    d.text((width//2, height-20), "AI Teacher", fill=(255,255,255,230), font=f, anchor="mt")
    return np.array(img)
