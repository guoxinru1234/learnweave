"""竞赛级教学视频渲染器 — 比赛答辩展示级别画质

风格: 玻璃拟态卡片 + 渐变背景 + AI 教师动画叠加
支持场景类型: intro / explain / key_point / confusion_point / summary / code
"""
import os, tempfile, math, numpy as np
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# ===== 兼容新版 Pillow =====
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

FFMPEG_PATH = r"D:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
if os.path.exists(FFMPEG_PATH):
    os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

# ==================== 色彩主题 ====================
THEME = {
    "bg_gradient_top": (10, 15, 35),
    "bg_gradient_bot": (25, 30, 55),
    "card_bg": (22, 28, 52),
    "card_border": (55, 60, 105),
    "accent": (99, 102, 241),       # indigo
    "accent2": (236, 72, 153),      # pink
    "gold": (250, 204, 21),
    "red": (239, 68, 68),
    "green": (34, 197, 94),
    "text_primary": (235, 240, 255),
    "text_secondary": (180, 190, 210),
    "text_muted": (120, 130, 160),
}

# ==================== 字体系统 ====================
_font_cache = {}

def _font(size: int) -> ImageFont.FreeTypeFont:
    key = f"default_{size}"
    if key not in _font_cache:
        for name in ["simhei.ttf", "msyh.ttf", "simsun.ttc", "arial.ttf"]:
            try:
                _font_cache[key] = ImageFont.truetype(name, size)
                break
            except Exception:
                continue
        if key not in _font_cache:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

# ==================== 中文文本排版 ====================

def _wrap_cn(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> list[str]:
    """逐字测量，精确换行。"""
    if not text:
        return [""]
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if font.getbbox(test)[2] - font.getbbox(test)[0] > max_width:
            if cur:
                lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines or [text]

def _clean_text(text: str) -> str:
    for p in ["[intro] ", "[Star] ", "[?] ", "[OK] ", "[explain] "]:
        text = text.replace(p, "")
    return text

# ==================== 渐变背景 ====================

def _draw_gradient_bg(draw: ImageDraw.Draw, W: int, H: int):
    """绘制深色渐变背景。"""
    for y in range(H):
        ratio = y / H
        r = int(THEME["bg_gradient_top"][0] * (1-ratio) + THEME["bg_gradient_bot"][0] * ratio)
        g = int(THEME["bg_gradient_top"][1] * (1-ratio) + THEME["bg_gradient_bot"][1] * ratio)
        b = int(THEME["bg_gradient_top"][2] * (1-ratio) + THEME["bg_gradient_bot"][2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

def _draw_top_bar(draw: ImageDraw.Draw, W: int):
    """顶部渐变装饰条。"""
    for i in range(4):
        alpha = 160 - i * 30
        draw.rectangle([0, i, W, i+1], fill=(99 + i*8, 102 + i*8, 241 - i*5))

def _draw_progress(draw: ImageDraw.Draw, W: int, H: int, idx: int, total: int):
    """底部进度指示器。"""
    dots_w = total * 12 + (total - 1) * 8
    start_x = W - 60 - dots_w
    y = H - 28
    for i in range(total):
        x = start_x + i * 20
        r = 4 if i == idx else 3
        color = THEME["accent"] if i == idx else THEME["text_muted"]
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
    # 页码文字
    draw.text((start_x - 50, y - 8), f"{idx+1}/{total}", fill=THEME["text_muted"], font=_font(14))

# ==================== 卡片绘制 ====================

def _draw_card(draw: ImageDraw.Draw, x1: int, y1: int, x2: int, y2: int,
               accent_color: tuple = None, emphasis: bool = False):
    """玻璃拟态卡片。"""
    if accent_color is None:
        accent_color = THEME["accent"]
    # 外发光
    if emphasis:
        for offset in range(6, 0, -2):
            alpha = 40 - offset * 5
            color = tuple(min(255, c + 30) for c in accent_color)
            draw.rounded_rectangle(
                [x1-offset, y1-offset, x2+offset, y2+offset],
                radius=20, outline=color
            )
    # 卡片主体
    draw.rounded_rectangle([x1, y1, x2, y2], radius=16,
                           fill=THEME["card_bg"], outline=accent_color, width=2)
    # 左侧装饰线
    draw.rectangle([x1 + 16, y1 + 24, x1 + 21, y2 - 24], fill=accent_color)

# ==================== 场景帧生成 ====================

def _make_frame(text: str, scene_type: str = "explain",
                emphasis: bool = False, code: str = None,
                idx: int = 0, total: int = 1) -> np.ndarray:
    """根据场景类型生成高质量帧。"""
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), THEME["bg_gradient_top"])
    draw = ImageDraw.Draw(img)

    # 渐变背景
    _draw_gradient_bg(draw, W, H)
    _draw_top_bar(draw, W)

    # 右上角 LearnWeave 品牌标识
    draw.text((W - 180, 22), "LearnWeave AI", fill=THEME["text_muted"], font=_font(16))

    # 场景类型图标和标签
    type_config = {
        "intro": ("", "课程引入", THEME["accent2"]),
        "key_point": ("", "核心重点", THEME["gold"]),
        "confusion_point": ("", "易混淆辨析", THEME["red"]),
        "summary": ("", "本讲总结", THEME["green"]),
        "explain": ("", "内容讲解", THEME["accent"]),
        "code": ("", "代码演示", (100, 210, 100)),
    }
    icon, label, a_color = type_config.get(scene_type, ("", "讲解", THEME["accent"]))
    clean = _clean_text(text)

    if scene_type == "code" and code:
        # ---- 代码演示风格 ----
        _draw_card(draw, 60, 80, W - 200, H - 90, accent_color=(100, 210, 100))
        draw.text((85, 95), f"{icon} {label}", fill=(100, 210, 100), font=_font(24))
        draw.line([(85, 130), (W - 250, 130)], fill=(50, 70, 50), width=1)

        # 说明文字
        if clean:
            draw.text((85, 145), "// " + clean[:70], fill=(140, 220, 140), font=_font(20))
        # 代码
        y = 180
        for cl in code.split('\n')[:18]:
            if y > H - 120:
                break
            color = (200, 220, 200)
            s = cl.strip()
            if s.startswith("//") or s.startswith("#"):
                color = (120, 180, 120)
            elif any(k in s for k in ["def ", "val ", "var ", "object ", "class ", "import "]):
                color = (200, 160, 255)
            elif any(k in s for k in ["if ", "else ", "for ", "while ", "match ", "case "]):
                color = (255, 190, 120)
            draw.text((95, y), cl[:75], fill=color, font=_font(17))
            y += 26

    else:
        # ---- 卡片式教学风格 ----
        card_x1, card_y1 = 55, 85
        card_x2, card_y2 = W - 195, H - 70
        _draw_card(draw, card_x1, card_y1, card_x2, card_y2,
                   accent_color=a_color, emphasis=emphasis)

        # 标签
        tag_x = card_x1 + 40
        draw.text((tag_x, card_y1 + 22), f"{icon} {label}", fill=a_color, font=_font(24))
        # 分割线
        split_y = card_y1 + 56
        draw.line([(tag_x, split_y), (card_x2 - 40, split_y)],
                  fill=tuple(int(c * 0.3) for c in a_color), width=1)

        # 正文排版
        content_x = tag_x + 5
        content_top = split_y + 24
        content_w = card_x2 - content_x - 30

        # 标题行（大字号）
        title_font = _font(38)
        title_lines = _wrap_cn(clean, content_w, title_font)
        title_text = title_lines[0] if title_lines else clean[:20]
        draw.text((content_x, content_top), title_text, fill=THEME["text_primary"], font=title_font)

        # 正文（如果有更多内容）
        if len(title_lines) > 1 or len(clean) > len(title_text):
            body_top = content_top + 58
            body_font = _font(28)
            remaining = clean[len(title_text):].strip()
            if len(title_lines) > 1:
                remaining = "".join(title_lines[1:]) + remaining
            body_lines = _wrap_cn(remaining, content_w, body_font)
            y = body_top
            for i, line in enumerate(body_lines[:6]):
                # 首行缩进
                prefix = "" if i > 0 else ""
                draw.text((content_x + 15, y), prefix + line, fill=THEME["text_secondary"], font=body_font)
                y += 44

            # 关键词高亮
            if emphasis and scene_type == "key_point":
                kw_y = y + 10
                keywords = ["不可变", "分布式", "容错", "缓存", "高性能", "并行"]
                kw_x = content_x + 15
                for kw in keywords:
                    if kw in clean:
                        kw_bbox = body_font.getbbox(kw)
                        kw_w = kw_bbox[2] - kw_bbox[0]
                        draw.rounded_rectangle(
                            [kw_x, kw_y, kw_x + kw_w + 16, kw_y + 30],
                            radius=6, fill=(250, 204, 21, 40), outline=THEME["gold"], width=1
                        )
                        draw.text((kw_x + 8, kw_y + 2), kw, fill=THEME["gold"], font=_font(20))
                        kw_x += kw_w + 28

    # 进度指示
    _draw_progress(draw, W, H, idx, total)

    return np.array(img)


# ==================== AI 教师水印 ====================

def _add_teacher_watermark(frame: np.ndarray) -> np.ndarray:
    """右下角 AI 教师小头像水印。"""
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    W, H = img.size
    r = 40
    cx, cy = W - r - 20, H - r - 15
    # 背景圆
    for i in range(r, 0, -1):
        alpha = int(80 * (i / r))
        draw.ellipse([cx-i, cy-i, cx+i, cy+i], fill=(79, 70, 229))
    # 头
    hr = 13
    draw.ellipse([cx-hr, cy-hr-3, cx+hr, cy+hr-3], fill=(252, 228, 200), outline=(200, 180, 160))
    for ex in [cx-5, cx+5]:
        draw.ellipse([ex-3, cy-hr-2, ex+3, cy-hr+4], fill=(40, 35, 30))
    draw.arc([cx-5, cy-hr+5, cx+5, cy-hr+13], start=0, end=180, fill=(200, 120, 130), width=1)
    # AI 标签
    draw.text((cx-18, cy+r+2), "AI", fill=(255, 255, 255), font=_font(11))
    return np.array(img)


# ==================== AI 教师动画（右侧） ====================

def _generate_animated_teacher_clip(duration: float, fps: int = 24,
                                     width: int = 220, height: int = 720):
    """Pillow 逐帧 AI 教师动画 — 校园女教师形象。

    外貌：浅蓝飘带雪纺衬衫 + 米白包臀裙 + 黑长直发 + 双手交叉腹前站姿
    气质：温柔知性、端庄得体、亲和力强
    """
    try:
        TF = ImageFont.truetype("simhei.ttf", 16)
        SF = ImageFont.truetype("simhei.ttf", 10)
    except Exception:
        TF = SF = ImageFont.load_default()

    # 色板
    SKIN = (255, 225, 195)        # 肤色
    SKIN_BORDER = (210, 175, 145)
    HAIR = (30, 25, 22)           # 乌黑秀发
    BLOUSE = (140, 185, 220)      # 浅蓝雪纺衬衫
    BLOUSE_DARK = (110, 155, 195)
    SKIRT = (245, 240, 230)       # 米白包臀裙
    SKIRT_DARK = (210, 200, 185)
    STOCKING = (235, 210, 185)    # 浅肤色丝袜
    SHOE = (180, 160, 140)        # 浅色低跟鞋
    BOW = (120, 170, 210)         # 领口蝴蝶结

    def make_frame(t):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # 微妙的呼吸和微动
        breath = math.sin(t * 0.9) * 2
        sway = math.sin(t * 0.35) * 1
        blink_t = math.sin(t * 0.55 + 2.0)
        is_blinking = blink_t > 0.90
        mouth_open = abs(math.sin(t * 1.8)) * 0.5 + 0.3

        bx = width // 2 + int(sway)
        by = 225 + int(breath)

        # ============ 身体比例 ============
        torso_w = 62
        torso_top = by + 75
        torso_bot = by + 230
        skirt_top = by + 205
        skirt_bot = by + 310

        # ============ 衬衫主体 ============
        d.polygon([
            (bx - torso_w, torso_top),
            (bx + torso_w, torso_top),
            (bx + torso_w + 6, skirt_top),
            (bx - torso_w - 6, skirt_top),
        ], fill=BLOUSE + (245,), outline=BLOUSE_DARK + (200,), width=1)

        # 衬衫中线/纽扣
        for by_pos in range(torso_top + 20, skirt_top - 10, 30):
            d.ellipse([bx - 2, by_pos - 2, bx + 2, by_pos + 2], fill=BLOUSE_DARK + (180,))

        # 领口 V 型
        d.polygon([
            (bx, torso_top),
            (bx - 25, torso_top + 38),
            (bx + 25, torso_top + 38),
        ], fill=BLOUSE + (200,), outline=BLOUSE_DARK + (180,), width=1)

        # ============ 简洁飘带蝴蝶结 ============
        bow_cx, bow_cy = bx, torso_top + 30
        # 左翼
        d.ellipse([bow_cx - 16, bow_cy - 5, bow_cx - 1, bow_cy + 8], fill=BOW + (220,))
        # 右翼
        d.ellipse([bow_cx + 1, bow_cy - 5, bow_cx + 16, bow_cy + 8], fill=BOW + (220,))
        # 中心小结
        d.ellipse([bow_cx - 4, bow_cy - 2, bow_cx + 4, bow_cy + 5], fill=BOW + (240,))
        # 飘带自然垂下（单条，简洁）
        d.polygon([
            (bow_cx - 5, bow_cy + 6),
            (bow_cx + 5, bow_cy + 6),
            (bow_cx + 4, bow_cy + 20),
            (bow_cx - 4, bow_cy + 20),
        ], fill=BOW + (200,))

        # ============ 包臀裙 ============
        skirt_left = bx - torso_w - 4
        skirt_right = bx + torso_w + 4
        d.polygon([
            (skirt_left, skirt_top),
            (skirt_right, skirt_top),
            (skirt_right + 8, skirt_bot),
            (skirt_left - 8, skirt_bot),
        ], fill=SKIRT + (240,), outline=SKIRT_DARK + (200,), width=1)

        # ============ 腿部（及膝裙下露出小腿） ============
        leg_top = skirt_bot
        leg_bot = by + 370
        # 左腿
        d.rectangle([bx - 18, leg_top, bx - 5, leg_bot], fill=STOCKING + (230,))
        # 右腿
        d.rectangle([bx + 5, leg_top, bx + 18, leg_bot], fill=STOCKING + (230,))

        # ============ 低跟鞋 ============
        shoe_y = leg_bot
        for sx, sd in [(bx - 14, -1), (bx + 14, 1)]:
            d.ellipse([sx - 14, shoe_y - 4, sx + 14, shoe_y + 6], fill=SHOE + (240,))
            d.ellipse([sx - 8, shoe_y - 6, sx + 12, shoe_y + 2], fill=SHOE + (200,))

        # ============ 头部 ============
        head_r = 42
        head_cx, head_cy = bx, by - 5
        # 脸部
        d.ellipse([head_cx - head_r, head_cy - head_r, head_cx + head_r, head_cy + head_r],
                  fill=SKIN + (255,), outline=SKIN_BORDER + (180,), width=2)

        # ============ 黑长直发（轻刘海，不遮脸） ============
        # 头顶秀发
        d.ellipse([head_cx - head_r - 4, head_cy - head_r - 6,
                   head_cx + head_r + 4, head_cy + head_r - 8],
                  fill=HAIR + (250,))
        # 轻薄空气刘海（只在额头最上方，不遮眉毛）
        d.rectangle([head_cx - head_r + 6, head_cy - head_r + 12,
                     head_cx + head_r - 6, head_cy - head_r + 20],
                    fill=HAIR + (180,))
        # 刘海微弧边缘
        for i in range(3):
            alpha = 160 - i * 40
            d.arc([head_cx - head_r + 8, head_cy - head_r + 8,
                   head_cx + head_r - 8, head_cy - head_r + 26],
                  start=190, end=350, fill=HAIR + (alpha,), width=1)
        # 两侧垂发（从耳后自然垂落肩头，不遮脸）
        hair_w = 15
        for sx in [head_cx - head_r - 2, head_cx + head_r - 14]:
            hair_len = 52
            # 垂发主体（从耳侧开始，在脸的外侧）
            d.rectangle([sx, head_cy - 2, sx + hair_w, head_cy + hair_len],
                        fill=HAIR + (230,))
            # 发尾自然微卷
            d.ellipse([sx - 2, head_cy + hair_len - 6, sx + hair_w + 2, head_cy + hair_len + 4],
                      fill=HAIR + (210,))
        # 头顶柔光
        d.arc([head_cx - 16, head_cy - head_r, head_cx + 16, head_cy - head_r + 16],
              start=210, end=330, fill=(70, 65, 60, 80), width=2)

        # ============ 眼睛（温和沉稳） ============
        eye_y = head_cy - 3
        for ex in [head_cx - 13, head_cx + 13]:
            if is_blinking:
                d.line([(ex - 8, eye_y), (ex + 8, eye_y)], fill=(50, 40, 35, 255), width=2)
            else:
                # 眼白
                d.ellipse([ex - 8, eye_y - 9, ex + 8, eye_y + 9],
                          fill=(255, 255, 255, 250), outline=(50, 40, 35, 230), width=2)
                # 瞳孔（大而温和）
                d.ellipse([ex - 3, eye_y - 2, ex + 4, eye_y + 6], fill=(45, 35, 30, 250))
                # 高光
                d.ellipse([ex - 1, eye_y - 7, ex + 3, eye_y - 3], fill=(255, 255, 255, 220))

        # ============ 细眉（柔和弧形） ============
        for ex in [head_cx - 13, head_cx + 13]:
            d.arc([ex - 10, eye_y - 20, ex + 10, eye_y - 10],
                  start=195, end=345, fill=(50, 40, 30, 170), width=2)

        # ============ 小巧鼻子 ============
        nose_y = eye_y + 13
        d.ellipse([head_cx - 3, nose_y - 1, head_cx + 3, nose_y + 6],
                  fill=SKIN_BORDER + (120,))

        # ============ 嘴巴（自然微扬微笑 + 说话动画） ============
        mouth_y = nose_y + 14
        mw = int(10 + mouth_open * 5)
        mh = int(5 + mouth_open * 6)
        # 上唇柔弧
        d.arc([head_cx - mw, mouth_y - 2, head_cx + mw, mouth_y + 6],
              start=0, end=180, fill=(195, 110, 120, 200), width=2)
        # 嘴角微扬（默认微笑状态）
        smile_dy = int(1 - mouth_open * 0.5)
        d.arc([head_cx - 13, mouth_y + smile_dy, head_cx + 13, mouth_y + 8 + smile_dy],
              start=200, end=340, fill=(185, 100, 110, 150), width=1)
        if mouth_open > 0.3:
            d.ellipse([head_cx - mw + 2, mouth_y + 2, head_cx + mw - 2, mouth_y + mh],
                      fill=(200, 120, 130, 180))

        # ============ 淡雅腮红 ============
        for sx in [head_cx - 25, head_cx + 25]:
            d.ellipse([sx - 8, eye_y + 10, sx + 8, eye_y + 22],
                      fill=(255, 180, 170, 50))

        # ============ 双手交叉腹前（端庄站姿） ============
        hand_y = skirt_top - 10
        # 左小臂（横过腹部）
        d.line([(bx - 30, torso_top + 60), (bx - 5, hand_y + 5), (bx + 15, hand_y)],
               fill=BLOUSE + (240,), width=14)
        # 右小臂（横过腹部，叠在左手上）
        d.line([(bx + 30, torso_top + 60), (bx + 5, hand_y + 3), (bx - 10, hand_y + 5)],
               fill=BLOUSE + (240,), width=14)
        # 交叠的双手
        d.ellipse([bx - 10, hand_y - 6, bx + 10, hand_y + 12],
                  fill=SKIN + (240,), outline=SKIN_BORDER + (150,), width=1)
        # 手指
        for fx in range(-6, 7, 4):
            d.line([(bx + fx, hand_y - 4), (bx + fx + 2, hand_y - 12)],
                   fill=SKIN + (220,), width=3)

        # ============ AI 胸牌（左胸） ============
        badge_x, badge_y = bx - torso_w + 5, torso_top + 15
        d.rounded_rectangle([badge_x, badge_y, badge_x + 42, badge_y + 20],
                            radius=4, fill=(255, 255, 255, 200),
                            outline=(100, 140, 180, 180), width=1)
        d.text((badge_x + 21, badge_y + 2), "AI 教师", fill=(100, 140, 180, 230), font=SF, anchor="mt")

        return np.array(img)

    return VideoClip(make_frame, duration=duration).set_fps(fps)


# ==================== 主渲染函数 ====================

def render_video_from_scenes(scenes: list, output_path: str = None,
                              style: str = "auto", fps: int = 24,
                              extra_clips: list = None) -> str:
    """渲染视频，支持嵌入额外的视频片段（如 Manim 动画）。

    scenes 中可以包含 type="manim" 的场景，指定 manim_path。
    也可通过 extra_clips 传入 (clip, insert_after_index) 列表。
    """
    if not scenes:
        raise ValueError("scenes 列表不能为空")
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "video_output.mp4")

    # 计算总时长（含额外片段）
    total_dur = sum(s.get("duration", 4) for s in scenes)
    manim_dur = 0
    if extra_clips:
        for clip, _ in extra_clips:
            manim_dur += clip.duration

    total_dur += manim_dur
    print(f"[START] 渲染视频: {len(scenes)} 场景 + {len(extra_clips or [])} 动画片段, 总长 {total_dur:.0f}s")

    teacher = _generate_animated_teacher_clip(duration=total_dur, fps=fps)
    print(f"[INFO] AI 教师动画: {total_dur:.0f}s")

    clips, cursor = [], 0.0
    total = len(scenes)

    for i, scene in enumerate(scenes):
        text = scene.get("text", "")
        stype = scene.get("type", "explain")
        emphasis = scene.get("emphasis", False)
        code = scene.get("code", None)
        dur = scene.get("duration", 4)
        manim_path = scene.get("manim_path", None)

        # 收集此场景后待插入的 Manim 动画
        manim_to_insert = []
        if extra_clips:
            for clip, after_idx in extra_clips:
                if after_idx == i:
                    manim_to_insert.append(clip)

        try:
            print(f"  [{i+1}/{total}] [{stype}] {text[:40]}...")
        except UnicodeEncodeError:
            pass

        # 如果有 Manim 且是"可视化演示"类型，直接用 Manim 视频
        if manim_path and os.path.exists(manim_path):
            try:
                mv = VideoFileClip(manim_path).resize(width=1000).set_position(("center", "center"))
                # 在 Manim 上叠加标题
                title_frame = _make_frame(text, "explain", idx=i, total=total)
                title_clip = ImageClip(title_frame).set_duration(mv.duration)
                combined = CompositeVideoClip([title_clip, mv.set_position(("center", 130))])
                combined = combined.set_duration(mv.duration)
                clips.append(combined)
                cursor += mv.duration
                continue
            except Exception as e:
                print(f"  [WARN] Manim load failed: {e}")

        # 生成背景帧 + AI 教师
        bg = _make_frame(text, stype, emphasis, code=code, idx=i, total=total)
        bg = _add_teacher_watermark(bg)

        try:
            tf = teacher.get_frame(cursor)
            if tf.shape[2] == 4:
                tr, ta = tf[:, :, :3], tf[:, :, 3:4] / 255.0
                h, w = bg.shape[:2]
                tw_ = tr.shape[1]
                reg = bg[:, w-tw_:w, :]
                bg[:, w-tw_:w, :] = (tr * ta + reg * (1 - ta)).astype(np.uint8)
        except Exception:
            pass

        clip = ImageClip(bg).set_duration(dur)
        if i > 0 and dur > 1.0:
            clip = clip.crossfadein(0.35)

        clips.append(clip)
        cursor += dur

        # 插入所有在此位置的 Manim 动画
        for mc in manim_to_insert:
            mc = mc.crossfadein(0.4).crossfadeout(0.3)
            clips.append(mc)
            cursor += mc.duration
            print(f"  [Manim] 插入动画片段 ({mc.duration:.1f}s)")

    full = concatenate_videoclips(clips, method="compose")
    print(f"[INFO] 编码输出: {output_path}")
    full.write_videofile(output_path, fps=fps, codec="libx264", audio_codec="aac",
                         ffmpeg_params=["-preset", "fast", "-crf", "18"],
                         verbose=False, logger=None)
    print(f"[OK] 视频生成完成: {output_path}")
    return output_path


def _load_loop_teacher_video():
    return "PILLOW_ANIMATED_TEACHER"


def render_demo_video() -> str:
    scenes = [
        {"text": "Python数据分析实战 —— 从零基础到数据科学家", "type": "intro", "duration": 3},
        {"text": "DataFrame 是 Pandas 的核心数据结构，提供灵活的数据操作能力", "type": "explain", "duration": 4},
        {"text": "广播变量：只读共享变量，缓存到每个 Executor 节点", "type": "key_point", "duration": 5, "emphasis": True},
        {"text": "广播变量 vs 累加器：一个只读共享，一个只写聚合", "type": "confusion_point", "duration": 5, "emphasis": True},
        {"text": "val conf = new SparkConf().setAppName(\"WordCount\")\nval sc = new SparkContext(conf)\nval rdd = sc.textFile(\"hdfs://...\")",
         "type": "code", "duration": 6},
        {"text": "掌握 groupby、merge 和 pivot_table，高效完成数据分析任务", "type": "summary", "duration": 4},
    ]
    return render_video_from_scenes(scenes, os.path.join(tempfile.gettempdir(), "demo_video.mp4"))
