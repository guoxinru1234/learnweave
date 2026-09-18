"""Generate the reproducible 50-case competition benchmark."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
COURSE_ID = "python-data-analysis"

PROFILES = [
    ("beginner", "非计算机专业大一，首次接触 Python", [12, 10, 15, 18, 35, 42], "basic"),
    ("theory", "计算机相关专业，概念理解较好但代码实践较少", [55, 35, 30, 48, 52, 60], "basic"),
    ("practice", "有脚本实践经验，数据处理理论不完整", [62, 72, 58, 55, 45, 50], "intermediate"),
    ("balanced", "完成过小型数据分析任务，各维度中等", [60, 62, 64, 60, 63, 65], "intermediate"),
    ("advanced", "有完整数据分析项目经验，关注性能和工程化", [86, 88, 84, 82, 87, 85], "advanced"),
]

TOPICS = [
    (1, "Python 环境搭建与 Jupyter 入门", ["Python 环境安装", "虚拟环境", "Jupyter Notebook", "单元格执行"]),
    (2, "Python 基础语法", ["变量与数据类型", "运算符", "条件与循环", "函数"]),
    (3, "NumPy 数组基础", ["ndarray", "数组创建", "索引与切片", "数组形状"]),
    (4, "NumPy 向量化计算", ["广播机制", "向量化运算", "聚合函数", "数组类型"]),
    (5, "Pandas Series 与 DataFrame", ["Series", "DataFrame", "索引", "表格数据结构"]),
    (6, "Pandas 数据筛选与合并", ["条件筛选", "loc 与 iloc", "groupby", "merge 与 concat"]),
    (7, "数据清洗与预处理", ["缺失值", "重复值", "异常值", "数据类型转换"]),
    (8, "Matplotlib 与 Seaborn 可视化", ["折线图", "柱状图", "坐标轴与标题", "图表展示"]),
    (9, "ETL 数据处理流程", ["Extract", "Transform", "Load", "读取整理保存"]),
    (10, "综合数据分析项目", ["提出问题", "数据整理", "统计分析", "结论表达"]),
]


def build_case(profile, topic):
    name, background, scores, level = profile
    lecture_num, title, points = topic
    case_id = f"{name}_{lecture_num:02d}"
    return {
        "case_id": case_id,
        "course_id": COURSE_ID,
        "lecture_num": lecture_num,
        "topic": title,
        "learner_profile": {
            "profile_type": name,
            "background": background,
            "dimensions": {
                "python_basic": scores[0], "coding_ability": scores[1],
                "data_processing": scores[2], "problem_solving": scores[3],
                "learning_habit": scores[4], "self_learning": scores[5],
            },
        },
        "expected": {
            "resource_level": level,
            "knowledge_points": points,
            "resource_types": ["lecture", "mindmap", "code", "practice"],
            "source": f"knowledge-base/{lecture_num:02d}/lecture.md",
        },
    }


def main():
    cases = [build_case(profile, topic) for profile in PROFILES for topic in TOPICS]
    assert len(cases) == 50
    with (ROOT / "cases.jsonl").open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    with (ROOT / "expected_labels.jsonl").open("w", encoding="utf-8") as f:
        for case in cases:
            label = {
                "case_id": case["case_id"],
                "resource_level": case["expected"]["resource_level"],
                "knowledge_points": case["expected"]["knowledge_points"],
                "source": case["expected"]["source"],
            }
            f.write(json.dumps(label, ensure_ascii=False) + "\n")
    print(f"generated {len(cases)} benchmark cases")


if __name__ == "__main__":
    main()
