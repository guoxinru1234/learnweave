"""Fix cached resource citations to use KB sources that actually support the content."""
import json, os

kb = "knowledge-base"
# Real sources that contain Jupyter/pip/conda content:
# 01 = Jupyter入门与Python环境, 02 = 变量与数据类型(has Jupyter+conda), 11 = Jupyter入门
# 20 = pip+环境, 64 = 模块化编程与包管理(pip)
fixed_cites = [
    {"title": "Jupyter入门与Python环境", "source": "knowledge-base/01/lecture.md"},
    {"title": "变量、数据类型与运算符", "source": "knowledge-base/02/lecture.md"},
    {"title": "NumPy数组创建与索引", "source": "knowledge-base/11/lecture.md"},
    {"title": "pip包管理与环境配置", "source": "knowledge-base/20/lecture.md"},
    {"title": "模块化编程与包管理", "source": "knowledge-base/64/lecture.md"},
]

# Verify all files exist
for c in fixed_cites:
    p = c["source"].replace("\\", "/")
    assert os.path.exists(p), f"MISSING: {p}"
print("All 5 citation files verified")

# Load and fix
with open("backend/data/lecture_cache/python-data-analysis_1_verified.json", encoding="utf-8") as f:
    real = json.load(f)

real["citations"] = fixed_cites

out = "backend/data/lecture_cache/python-data-analysis_1_verified_fixed.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(real, f, ensure_ascii=False, indent=2)
print(f"Fixed resource saved: {out}")
