"""Manim 教学视频生成器 — 每分镜场景渲染为 Manim 动画片段

替代 Pillow 静态帧，用 Manim 的数学排版 + 动画效果生成高质量黑板内容。
"""
import os, tempfile, subprocess, shutil, re
from typing import Optional

_MANIM_EXE = None

def _find_manim() -> str | None:
    """查找 Manim 可执行文件。"""
    global _MANIM_EXE
    if _MANIM_EXE:
        return _MANIM_EXE
    # 尝试常见路径
    candidates = [
        shutil.which("manim"),
        shutil.which("manimgl"),
        shutil.which("manimce"),
    ]
    # 也检查 venv 里的
    import sys
    venv_manim = os.path.join(os.path.dirname(sys.executable), "manim.exe")
    if os.path.exists(venv_manim):
        candidates.insert(0, venv_manim)

    for c in candidates:
        if c and os.path.exists(c):
            _MANIM_EXE = c
            return c
    return None


def _build_manim_script(scenes: list, output_dir: str) -> str:
    """根据分镜列表生成 Manim Python 脚本文件。

    每个场景渲染为一段动画：标题渐入 → 正文逐字 → 关键点高亮 → 淡出。
    返回 .py 脚本路径。
    """
    lines = [
        '"""LearnWeave AI 教学视频 — Manim 自动生成"""',
        'from manim import *',
        'import numpy as np',
        '',
        'config.pixel_height = 720',
        'config.pixel_width = 1080  # 左侧黑板区域，右侧留给AI教师',
        'config.frame_rate = 24',
        'config.background_color = "#0A0F23"',
        '',
        'class TeachingVideo(Scene):',
        '    def construct(self):',
    ]

    accent_map = {
        "intro": "BLUE",
        "key_point": "YELLOW",
        "confusion_point": "RED",
        "summary": "GREEN",
        "explain": "TEAL",
    }

    for i, scene in enumerate(scenes):
        text = scene.get("text", "")
        stype = scene.get("type", "explain")
        dur = scene.get("duration", 4)
        accent = accent_map.get(stype, "BLUE_C")

        # 清理文本前缀
        clean = text
        for p in ["[intro] ", "[Star] ", "[?] ", "[OK] ", "[explain] "]:
            clean = clean.replace(p, "")

        # 标签
        labels = {"intro": "课程引入", "key_point": "核心重点", "confusion_point": "易混淆辨析",
                  "summary": "本讲总结", "explain": "内容讲解"}
        label = labels.get(stype, "内容")

        # 按长度拆分为标题行和正文行（Manim 会自动排版）
        if len(clean) <= 30:
            main_text = clean
            sub_text = ""
        else:
            main_text = clean[:30]
            sub_text = clean[30:]

        lines.append(f'')
        lines.append(f'        # ===== 场景 {i+1}: [{stype}] {label} =====')
        lines.append(f'')
        lines.append(f'        # 标题标签')
        lines.append(f'        tag = Text("{label}", font="SimHei", font_size=22, color={accent})')
        lines.append(f'        tag.to_corner(UL, buff=0.4)')
        lines.append(f'        self.play(FadeIn(tag, shift=UP * 0.3), run_time=0.4)')
        lines.append(f'')

        # 主标题
        escaped_main = main_text.replace('"', '\\"')
        lines.append(f'        title = Text("{escaped_main}", font="SimHei", font_size=36, color=WHITE, line_spacing=1.5)')
        lines.append(f'        title.move_to(ORIGIN + UP * 0.5)')
        lines.append(f'        self.play(Write(title), run_time=1.2)')
        lines.append(f'        self.wait(0.3)')

        # 副文本（如有）
        if sub_text:
            escaped_sub = sub_text.replace('"', '\\"')
            lines.append(f'')
            lines.append(f'        body = Text("{escaped_sub}", font="SimHei", font_size=28, color=LIGHT_GRAY, line_spacing=1.8)')
            lines.append(f'        body.next_to(title, DOWN, buff=0.5)')
            lines.append(f'        self.play(FadeIn(body, shift=DOWN * 0.2), run_time=1.0)')

        # 重点场景加视觉强调
        if stype == "key_point":
            lines.append(f'')
            lines.append(f'        # 重点：金色边框闪烁')
            lines.append(f'        highlight = SurroundingRectangle(title, color={accent}, buff=0.3, corner_radius=0.2)')
            lines.append(f'        self.play(Create(highlight), run_time=0.5)')
            lines.append(f'        self.play(Flash(title, color=YELLOW, line_length=0.3), run_time=0.5)')
        elif stype == "confusion_point":
            lines.append(f'')
            lines.append(f'        # 易混淆：红色警示条')
            lines.append(f'        warn_bar = Rectangle(height=0.08, width=config.frame_width-2, color={accent}, fill_opacity=0.3)')
            lines.append(f'        warn_bar.to_edge(LEFT, buff=1)')
            lines.append(f'        warn_bar.shift(UP * 3)')
            lines.append(f'        self.play(FadeIn(warn_bar), run_time=0.4)')

        # 场景停留时间
        wait_time = max(0.8, dur - 2.0)
        lines.append(f'        self.wait({wait_time:.1f})')

        # 淡出（最后场景除外）
        if i < len(scenes) - 1:
            lines.append(f'')
            lines.append(f'        # 过渡到下一场景')
            lines.append(f'        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)')

    # 结尾
    lines.append(f'')
    lines.append(f'        # 结尾标识')
    lines.append(f'        branding = Text("LearnWeave AI", font="SimHei", font_size=20, color=GREY)')
    lines.append(f'        branding.to_corner(DR, buff=0.5)')
    lines.append(f'        self.play(FadeIn(branding), run_time=0.5)')
    lines.append(f'        self.wait(0.5)')

    # 写入文件
    script_path = os.path.join(output_dir, "teaching_scene.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return script_path


def render_manim_scenes(scenes: list, output_path: str = None,
                         quality: str = "medium") -> str | None:
    """用 Manim 渲染分镜场景为视频片段。

    Args:
        scenes: 分镜列表
        output_path: 输出 mp4 路径
        quality: "low" (480p), "medium" (720p), "high" (1080p)

    Returns:
        生成的视频文件路径，失败返回 None
    """
    manim_exe = _find_manim()
    if not manim_exe:
        print("[ManimRenderer] Manim 未安装，跳过")
        return None

    work_dir = tempfile.mkdtemp(prefix="manim_render_")
    try:
        script = _build_manim_script(scenes, work_dir)
        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(quality, "-qm")

        print(f"[ManimRenderer] 渲染中... ({len(scenes)} 场景, quality={quality})")
        result = subprocess.run(
            [manim_exe, quality_flag, "--disable_caching", script, "TeachingVideo"],
            cwd=work_dir, capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            print(f"[ManimRenderer] 渲染失败: {result.stderr[-300:]}")
            # 尝试用 pilllow 降级？
            return None

        # 查找生成的视频文件
        for root, dirs, files in os.walk(work_dir):
            for f in files:
                if f.endswith(".mp4") and "TeachingVideo" in f:
                    src = os.path.join(root, f)
                    if output_path is None:
                        return src
                    shutil.copy2(src, output_path)
                    print(f"[ManimRenderer] 完成: {output_path}")
                    return output_path

        print("[ManimRenderer] 未找到输出视频文件")
        return None
    except subprocess.TimeoutExpired:
        print("[ManimRenderer] 渲染超时 (>5min)")
        return None
    except Exception as e:
        print(f"[ManimRenderer] 错误: {e}")
        return None
