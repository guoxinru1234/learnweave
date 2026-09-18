# backend/app/core/video_composer.py
import os
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

def compose_video_with_teacher(
    scenes: list,
    teacher_path: str = "media/videos/teacher_loop.mov",
    output_path: str = None
) -> str:
    if output_path is None:
        output_path = os.path.join("media", "videos", "output_final.mp4")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("[VideoComposer] Starting composition...")

    # 1. 加载老师视频
    if not os.path.exists(teacher_path):
        raise FileNotFoundError(f"老师视频不存在: {teacher_path}")

    teacher_clip = VideoFileClip(teacher_path)
    if teacher_clip.audio is None:
        teacher_clip = teacher_clip.set_audio(None)
    teacher_duration = teacher_clip.duration
    print(f"📹 老师视频加载成功，时长: {teacher_duration}s，分辨率: {teacher_clip.size}")

    # 2. 计算板子位置（左上角 60%）
    width, height = teacher_clip.size
    board_width = int(width * 0.6)
    board_height = int(height * 0.6)
    board_x = 0
    board_y = 0

    print(f"📐 蓝色板子区域: ({board_x}, {board_y}) 到 ({board_width}, {board_height})")

    # 3. 为每个场景生成带文字的画面
    text_clips = []
    total_duration = 0

    for i, scene in enumerate(scenes):
        duration = scene.get('duration', 3)
        text = scene.get('text', '')
        scene_type = scene.get('type', 'explain')
        emphasis = scene.get('emphasis', False)

        print(f"  场景 {i+1}: {scene_type} - {text[:30]}...")

        text_img = create_text_frame(
            text=text,
            scene_type=scene_type,
            emphasis=emphasis,
            width=board_width,
            height=board_height
        )

        img_clip = ImageClip(text_img).set_duration(duration)
        text_clips.append(img_clip)
        total_duration += duration

    # 4. 组合所有文字场景
    text_sequence = concatenate_videoclips(text_clips, method="compose")

    # 5. 处理老师视频长度：手动循环
    if teacher_duration < total_duration:
        repeats = int(total_duration // teacher_duration) + 1
        looped_clips = [teacher_clip] * repeats
        teacher_clip = concatenate_videoclips(looped_clips).subclip(0, total_duration)
    else:
        teacher_clip = teacher_clip.subclip(0, total_duration)

    # 6. 文字画面已正确尺寸，直接设置位置
    text_sequence = text_sequence.set_position((board_x, board_y))

    # 7. 合成最终视频
    print("🔄 正在合成最终视频...")
    final = CompositeVideoClip([
        teacher_clip,
        text_sequence
    ])

    # 8. 导出
    final.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac' if teacher_clip.audio is not None else None,
        ffmpeg_params=['-preset', 'fast', '-crf', '23'],
        verbose=False,
        logger=None
    )

    print(f"[OK] 合成完成: {output_path}")
    return output_path


def create_text_frame(text: str, scene_type: str, emphasis: bool, width: int, height: int) -> np.ndarray:
    """
    生成单帧文字画面（透明背景）
    [OK] 统一白色文字
    [OK] 位置右移（x=70），下移（y=120）
    """
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 统一白色
    color = '#ffffff'
    font_size = 40

    # 用 emoji 标签代替彩色文字
    label = ""
    if scene_type == 'intro':
        label = "[Book] "
    elif scene_type == 'key_point' and emphasis:
        label = "[Star] "
    elif scene_type == 'confusion_point' and emphasis:
        label = "[?] "
    elif scene_type == 'summary':
        label = "[OK] "

    try:
        font = ImageFont.truetype("simhei.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # 清理文字
    clean_text = text
    for prefix in ["[Book] ", "[Star] ", "[?] ", "[OK] "]:
        if clean_text.startswith(prefix):
            clean_text = clean_text[len(prefix):].strip()
            break

    final_text = label + clean_text

    max_chars = 20
    lines = wrap_text(final_text, max_chars)

    x_start = 70
    y = 120
    for line in lines:
        draw.text((x_start, y), line, fill=color, font=font)
        y += font_size + 8

    return np.array(img)


def wrap_text(text: str, max_chars: int = 20) -> list:
    """
    智能换行，优先在标点符号后断行，保护英文单词完整
    """
    if not text:
        return ['']
    if len(text) <= max_chars:
        return [text]

    # 中文标点 + 英文标点
    punct = set('，。、；：！？,.;:!?')
    lines = []
    start = 0

    while start < len(text):
        if len(text) - start <= max_chars:
            lines.append(text[start:].strip())
            break

        end = start + max_chars
        found = -1

        for i in range(end, start, -1):
            if i < len(text) and (text[i-1] in punct or text[i-1] == ' '):
                found = i
                break

        if found == -1:
            # 没有标点，检查英文单词
            j = start + max_chars
            if j < len(text) and text[j].isalpha() and text[j].isascii():
                # 向后找单词结束
                while j < len(text) and text[j].isalpha() and text[j].isascii():
                    j += 1
                if j - start <= max_chars + 5:
                    lines.append(text[start:j].strip())
                    start = j
                    continue

            # 强制切割
            lines.append(text[start:start+max_chars].strip())
            start = start + max_chars
        else:
            lines.append(text[start:found].strip())
            start = found

    lines = [line.strip() for line in lines if line.strip()]

    # 最后一行太短时合并
    if len(lines) > 1 and len(lines[-1]) <= 3:
        last = lines.pop()
        if len(lines[-1]) + len(last) <= max_chars + 2:
            lines[-1] += last
        else:
            lines.append(last)

    return lines


def render_demo_with_teacher():
    scenes = [
        {"text": "[Book] Pandas 数据处理基础", "type": "intro", "duration": 3},
        {"text": "DataFrame 是 Pandas 最核心的数据结构", "type": "explain", "duration": 4},
        {"text": "[Star] 广播变量：只读共享变量，缓存到 Executor", "type": "key_point", "duration": 4, "emphasis": True},
        {"text": "[Star] 累加器：只写共享变量，用于聚合统计", "type": "key_point", "duration": 4, "emphasis": True},
        {"text": "[?] 广播变量 vs 累加器：一个只读，一个只写", "type": "confusion_point", "duration": 5, "emphasis": True},
        {"text": "[OK] 掌握 groupby 和 pivot，高效处理数据", "type": "summary", "duration": 3},
    ]
    return compose_video_with_teacher(scenes)