"""Manim 教学动画生成服务 — LearnWeave Python 数据分析课程"""
import os, sys, subprocess, tempfile

MANIM_SCRIPT = '''
from manim import config
config.background_color = "#0f172a"
config.frame_width = 14
config.frame_height = 8

from manim import *

P = "#818cf8"   # primary
A = "#4f46e5"   # accent
G = "#34d399"   # green
Y = "#fbbf24"   # yellow
R = "#f87171"   # red
W = "#e2e8f0"   # white
D = "#1e293b"   # dark

def boxed(text, color, w=2.2, h=1.0):
    rect = RoundedRectangle(width=w, height=h, corner_radius=0.15, fill_opacity=0.3, fill_color=color, stroke_color=color)
    label = Text(text, font_size=20, color=W)
    label.move_to(rect)
    return VGroup(rect, label)

def title_line(text):
    t = Text(text, font_size=38, color=P)
    t.to_edge(UP, buff=0.5)
    u = Line(LEFT*6, RIGHT*6, color=A, stroke_width=2).next_to(t, DOWN, buff=0.15)
    return VGroup(t, u)


class PandasGroupBy(Scene):
    def construct(self):
        self.play(Write(title_line("Pandas 操作: groupby / merge / pivot_table")[0]),
                  GrowFromCenter(title_line("")[1]))
        src = VGroup(*[boxed(str(i), Y, 1.0, 1.0) for i in range(1,6)])
        src.arrange(RIGHT, buff=0.4).shift(UP*1.5)
        lbl = Text("原始 DataFrame 数据", font_size=22, color=W).next_to(src, UP, buff=0.3)
        self.play(Write(lbl), LaggedStart(*[FadeIn(b, scale=0.8) for b in src], lag_ratio=0.1))
        self.wait(0.3)

        op = boxed("map: x -> x*2", G, 5.5, 0.8).shift(UP*0.1)
        self.play(FadeIn(op))
        dst = VGroup(*[boxed(str(i*2), G, 1.0, 1.0) for i in range(1,6)])
        dst.arrange(RIGHT, buff=0.4).shift(DOWN*1.2)
        self.play(LaggedStart(*[FadeIn(b, scale=0.8) for b in dst], lag_ratio=0.1))
        self.wait(0.8)
        self.play(FadeOut(op), FadeOut(src), FadeOut(lbl))

        op2 = boxed("filter: 保留 >5 的元素", R, 5.5, 0.8).shift(UP*0.1)
        self.play(FadeIn(op2))
        for i in [0,1,2]:
            self.play(dst[i].animate.set_opacity(0.15), run_time=0.2)
        self.play(dst[3:].animate.shift(UP*0.5))
        self.wait(0.5)

        tip = Text("转化操作是惰性的, 只构建 DAG 不立即执行", font_size=22, color=Y, font="SimHei")
        tip.to_edge(DOWN, buff=0.4)
        self.play(Write(tip))
        self.wait(2)


class PandasMerge(Scene):
    def construct(self):
        self.play(Write(title_line("Pandas groupby 聚合过程")[0]))
        stages = [
            ("Map 阶段: 每个 Partition 按 Key 排序后写入磁盘 (Shuffle Write)", G, 2.5),
            ("网络传输: 相同 Key 的数据发送到同一个 Reducer", Y, 0.8),
            ("Reduce 阶段: 拉取数据 + 按键合并 + 执行计算 (Shuffle Read)", R, -1.0),
        ]
        for label, color, y in stages:
            r = RoundedRectangle(width=12, height=1.0, corner_radius=0.15, fill_opacity=0.25, fill_color=color, stroke_color=color)
            r.shift(UP*y)
            t = Text(label, font_size=20, color=W, font="SimHei").move_to(r)
            self.play(FadeIn(r), Write(t), run_time=0.6)
            self.wait(0.4)
        tip = Text("优化建议: 用 reduceByKey 替代 groupByKey, 先在 Map 端预聚合减少 Shuffle 数据量", font_size=18, color=G, font="SimHei")
        tip.to_edge(DOWN, buff=0.4)
        self.play(Write(tip))
        self.wait(2)


class BroadcastVariable(Scene):
    def construct(self):
        self.play(Write(title_line("广播变量 Broadcast")[0]))
        drv = RoundedRectangle(width=3, height=2.5, corner_radius=0.15, fill_opacity=0.2, fill_color=A, stroke_color=P)
        drv.shift(LEFT*4.5 + UP*0.3)
        self.play(FadeIn(drv), Write(Text("Driver", font_size=22, color=W).move_to(drv.get_top()+DOWN*0.5)))
        self.play(Write(Text("共享数据 data = {...}", font_size=18, color=Y, font="SimHei").move_to(drv)))
        self.wait(0.5)

        bad = Text("未使用广播: 每个 Task 拷贝一份完整数据", font_size=18, color=R, font="SimHei")
        bad.shift(RIGHT*3 + UP*2.5)
        self.play(Write(bad))
        execs = VGroup()
        for i in range(3):
            e = RoundedRectangle(width=2, height=1.2, corner_radius=0.1, fill_opacity=0.15, fill_color=D, stroke_color="#475569")
            e.move_to(RIGHT*2.5 + RIGHT*i*2.2 + UP*0.5)
            self.play(FadeIn(e), Write(Text(f"Executor {i+1}", font_size=14, color="#94a3b8").move_to(e)), run_time=0.3)
        self.wait(1)
        self.play(FadeOut(bad), FadeOut(execs))

        good = Text("使用广播: 每个 Executor 缓存一份, Task 共享引用", font_size=18, color=G, font="SimHei")
        good.shift(RIGHT*3 + UP*2.5)
        self.play(Write(good))
        a = Arrow(drv.get_right(), RIGHT*1.5 + UP*0.5, color=G, max_tip_length_to_length_ratio=0.15)
        self.play(GrowArrow(a), Write(Text("broadcast()", font_size=14, color=G).next_to(a, UP, buff=0.1)))
        for i in range(3):
            e = RoundedRectangle(width=2, height=1.2, corner_radius=0.1, fill_opacity=0.2, fill_color=G, stroke_color=G)
            e.move_to(RIGHT*2.5 + RIGHT*i*2.2 + UP*0.5)
            label = VGroup(Text(f"Executor {i+1}", font_size=13, color=W), Text("共享引用", font_size=13, color=G, font="SimHei")).arrange(DOWN, buff=0.1).move_to(e)
            self.play(FadeIn(e), Write(label), run_time=0.3)

        tip = Text("100 个 Executor × 10000 个 Task → 节省约 10000 倍数据传输", font_size=20, color=Y, font="SimHei")
        tip.to_edge(DOWN, buff=0.4)
        self.play(Write(tip))
        self.wait(2)


class DataFramePipeline(Scene):
    def construct(self):
        self.play(Write(title_line("Pandas 数据处理管道")[0]))
        stages = [
            ("Stage 1: DataFrame", G, LEFT*5 + UP*1.2),
            ("Stage 2: map/filter", G, LEFT*1.5 + UP*1.2),
            ("Stage 3: Shuffle", R, RIGHT*2 + UP*1.2),
            ("Stage 4: reduceByKey", A, RIGHT*5.5 + UP*1.2),
            ("Stage 5: 输出", P, RIGHT*1.5 + DOWN*1.5),
        ]
        prev = None
        for label, color, pos in stages:
            b = RoundedRectangle(width=2.6, height=1.0, corner_radius=0.15, fill_opacity=0.3, fill_color=color, stroke_color=color)
            b.move_to(pos)
            t = Text(label, font_size=18, color=W, font="SimHei").move_to(b)
            self.play(FadeIn(b), Write(t), run_time=0.4)
            if prev:
                arr = Arrow(prev.get_right()+RIGHT*0.1, b.get_left()+LEFT*0.1, color="#64748b",
                           max_tip_length_to_length_ratio=0.1)
                if "Shuffle" in label: arr.set_color(R)
                self.play(GrowArrow(arr), run_time=0.2)
            prev = b

        self.play(Write(Text("窄依赖 Stage 1->2 (pipeline, 无Shuffle)", font_size=16, color=G, font="SimHei").shift(LEFT*3.3+DOWN*0.3)))
        self.play(Write(Text("宽依赖 Stage 2->3 (触发Shuffle)", font_size=16, color=R, font="SimHei").shift(RIGHT*2+DOWN*0.3)))
        self.wait(2)
'''

# ===== Dynamic Manim animations (LLM-generated) =====
# The following animation topics are generated dynamically by ManimAgent
# using Xfyun LLM. See manim_agent.py for the generation pipeline.

# Removed corrupted preset animations. Use ManimAgent for:
# - scala_pattern_match
# - scala_collections
# - spark_sql_dataframe
# - spark_ml_pipeline
# - spark_streaming


class ManimService:
    ANIMATIONS = {
        "pandas_groupby": {"class": "PandasGroupBy"},
        "pandas_merge": {"class": "PandasMerge"},
        "broadcast": {"class": "BroadcastVariable"},
        "dataframe_pipeline": {"class": "DataFramePipeline"},
    }

    # Topics for LLM dynamic generation (via ManimAgent)
    DYNAMIC_TOPICS = [
        "scala_pattern_match",
        "scala_collections",
        "spark_sql_dataframe",
        "spark_ml_pipeline",
        "spark_streaming",
    ]

    def __init__(self, quality: str = "l"):
        self.quality = quality
        self._manim_exe = self._find_manim()

    def _find_manim(self) -> str:
        # Priority 1: manim.exe next to python.exe in Scripts/ (Windows)
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
        venv_manim = os.path.join(scripts_dir, "manim.exe")
        if os.path.exists(venv_manim):
            return venv_manim
        # Priority 2: manim.exe next to python.exe (Linux/macOS venv)
        venv_manim = os.path.join(os.path.dirname(sys.executable), "manim.exe")
        if os.path.exists(venv_manim):
            return venv_manim
        # Priority 3: system PATH
        import shutil
        found = shutil.which("manim")
        if found:
            return found
        return "manim"

    def generate(self, name: str, output_path: str = None) -> str | None:
        if name not in self.ANIMATIONS:
            raise ValueError(f"Unknown: {name}. Options: {list(self.ANIMATIONS)}")
        info = self.ANIMATIONS[name]
        if output_path is None:
            output_path = f"media/videos/manim_{name}.mp4"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        script_path = os.path.join(tempfile.gettempdir(), f"manim_{name}.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(MANIM_SCRIPT)

        cmd = [self._manim_exe, f"-q{self.quality}", script_path, info["class"],
               "-o", os.path.basename(output_path)]
        print(f"[Manim] {name}...")
        try:
            r = subprocess.run(cmd, cwd=os.path.dirname(output_path) or ".", capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                err = r.stderr[-300:] if r.stderr else ""
                print(f"[Manim] Error: {err}")
                return None
            # Copy output from manim subdir (quality: l=480p15, m=720p30, h=1080p60)
            qdir = {"l": "480p15", "m": "720p30", "h": "1080p60"}.get(self.quality, "720p30")
            manim_out = os.path.join(os.path.dirname(output_path) or ".",
                                     "media", "videos", f"manim_{name}", qdir, os.path.basename(output_path))
            if os.path.exists(manim_out):
                import shutil; shutil.copy(manim_out, output_path)
            print(f"[Manim] OK: {output_path}")
            return output_path
        except subprocess.TimeoutExpired:
            print("[Manim] Timeout")
            return None

    def generate_all(self, out_dir: str = "media/videos") -> dict:
        results = {}
        for name in self.ANIMATIONS:
            results[name] = self.generate(name, os.path.join(out_dir, f"manim_{name}.mp4"))
        return results


async def render_script(script: str, class_name: str, output_path: str, quality: str = "l") -> bool:
    """渲染动态生成的 Manim 脚本（供 ManimAgent 调用）"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _render_sync, script, class_name, output_path, quality)


def _render_sync(script: str, class_name: str, output_path: str, quality: str) -> bool:
    """同步渲染 Manim 脚本"""
    script_path = os.path.join(tempfile.gettempdir(), f"manim_dynamic_{class_name}.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    import sys, glob, shutil
    # Find manim executable (same logic as _find_manim)
    scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    manim_exe = os.path.join(scripts_dir, "manim.exe")
    if not os.path.exists(manim_exe):
        manim_exe = os.path.join(os.path.dirname(sys.executable), "manim.exe")
    if not os.path.exists(manim_exe):
        found = shutil.which("manim")
        manim_exe = found if found else "manim"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Run manim from tempdir to avoid nested media/videos paths
    work_dir = tempfile.mkdtemp(prefix="manim_render_")
    cmd = [manim_exe, f"-q{quality}", script_path, class_name]
    try:
        r = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            # Try to find partial output anyway
            pass

        # Find the rendered MP4 in manim's output tree
        qdir = {"l": "480p15", "m": "720p30", "h": "1080p60"}.get(quality, "480p15")
        pattern = os.path.join(work_dir, "media", "videos", "manim_dynamic_*", qdir, "*.mp4")
        candidates = glob.glob(pattern)
        if candidates:
            shutil.copy(candidates[0], output_path)
            print(f"[Manim] Rendered: {output_path} ({os.path.getsize(output_path)} bytes)")
            return True

        # Fallback: search entire work_dir
        for root, dirs, files in os.walk(work_dir):
            for f in files:
                if f.endswith(".mp4"):
                    shutil.copy(os.path.join(root, f), output_path)
                    print(f"[Manim] Rendered (fallback): {output_path}")
                    return True

        if r.returncode != 0:
            print(f"[Manim] Render error: {r.stderr[-300:]}")
        return False
    except subprocess.TimeoutExpired:
        print("[Manim] Timeout")
        return False
