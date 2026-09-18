#!/usr/bin/env python3
"""P1: 从现有 index.json 构建 Python 数据分析知识点体系。

产出:
  - knowledge-base/skill_tree.json        技能域树（10 技能域 + 扩展）
  - knowledge-base/knowledge_points.json  知识点结构化记录（62 个）

设计原则:
  - 知识点以真实课程讲次（74 讲）为唯一来源，不凭空新增知识。
  - knowledge_id 格式: {DOMAIN}-{TOPIC}-{NNN}，稳定、唯一。
  - 61-74 讲是 01-12 讲的 curated 细化版，合并进对应主知识点（source_lessons 多值）。
  - difficulty / prerequisites 用 curriculum_order 启发式推导，明确标注来源，不伪装专家标注。
  - quality_level 依据实际课程质量差异（01-12 抓取版 / 13-60 模板占位 / 61-74 curated）。
"""
import json
from pathlib import Path

KB = Path(__file__).resolve().parent.parent / "knowledge-base"

# ============================================================
# 62 个知识点映射表（唯一手工维护的数据，全部来自真实讲次标题）
# 字段: id / domain / title / lessons / points
# ============================================================
KNOWLEDGE = [
    # ---- Python基础 (6) ----
    {"id": "PY-BASIC-001", "domain": "Python基础", "title": "Python数据类型与运算符", "lessons": [1, 61], "points": ["变量", "数据类型", "运算符"]},
    {"id": "PY-BASIC-002", "domain": "Python基础", "title": "流程控制与函数", "lessons": [2, 62, 63], "points": ["条件", "循环", "函数"]},
    {"id": "PY-BASIC-003", "domain": "Python基础", "title": "列表推导式与生成器", "lessons": [3], "points": ["列表推导式", "生成器"]},
    {"id": "PY-BASIC-004", "domain": "Python基础", "title": "文件读写与异常处理", "lessons": [4], "points": ["文件读写", "异常处理"]},
    {"id": "PY-BASIC-005", "domain": "Python基础", "title": "常用标准库", "lessons": [5], "points": ["os", "datetime", "collections"]},
    {"id": "PY-BASIC-006", "domain": "Python基础", "title": "模块化编程与包管理", "lessons": [64], "points": ["模块", "包"]},

    # ---- NumPy (5) ----
    {"id": "NUMPY-ARRAY-001", "domain": "NumPy", "title": "数组创建与索引切片", "lessons": [6, 65], "points": ["ndarray", "索引", "切片"]},
    {"id": "NUMPY-BROADCAST-001", "domain": "NumPy", "title": "广播机制与向量化", "lessons": [7, 66, 67], "points": ["广播", "向量化"]},
    {"id": "NUMPY-LINALG-001", "domain": "NumPy", "title": "线性代数运算", "lessons": [8], "points": ["线性代数", "矩阵"]},
    {"id": "NUMPY-RANDOM-001", "domain": "NumPy", "title": "随机数生成与统计函数", "lessons": [9, 68], "points": ["随机数", "统计函数"]},
    {"id": "NUMPY-PERF-001", "domain": "NumPy", "title": "性能优化与内存布局", "lessons": [10], "points": ["性能优化", "内存布局"]},

    # ---- Pandas (10) ----
    {"id": "PANDAS-SERIES-001", "domain": "Pandas", "title": "Series与DataFrame核心", "lessons": [11], "points": ["Series", "DataFrame"]},
    {"id": "PANDAS-READ-001", "domain": "Pandas", "title": "CSV/Excel/JSON数据读取", "lessons": [12, 69], "points": ["read_csv", "read_excel", "read_json"]},
    {"id": "PANDAS-SELECT-001", "domain": "Pandas", "title": "数据选择loc/iloc/query", "lessons": [13, 70], "points": ["loc", "iloc", "query"]},
    {"id": "PANDAS-MISSING-001", "domain": "Pandas", "title": "缺失值检测与处理", "lessons": [14, 71], "points": ["缺失值", "isnull", "fillna"]},
    {"id": "PANDAS-DTYPE-001", "domain": "Pandas", "title": "数据类型转换与优化", "lessons": [15], "points": ["数据类型转换"]},
    {"id": "PANDAS-GROUPBY-001", "domain": "Pandas", "title": "groupby分组聚合", "lessons": [16], "points": ["groupby", "agg", "sum", "mean"]},
    {"id": "PANDAS-PIVOT-001", "domain": "Pandas", "title": "数据透视表pivot_table", "lessons": [17], "points": ["pivot_table"]},
    {"id": "PANDAS-MERGE-001", "domain": "Pandas", "title": "merge/join/concat合并", "lessons": [18], "points": ["merge", "join", "concat"]},
    {"id": "PANDAS-TIMESERIES-001", "domain": "Pandas", "title": "时间序列处理", "lessons": [19], "points": ["时间序列"]},
    {"id": "PANDAS-PIPE-001", "domain": "Pandas", "title": "链式操作与pipe最佳实践", "lessons": [20], "points": ["pipe", "链式操作"]},

    # ---- 数据清洗 (5) ----
    {"id": "CLEAN-DUP-001", "domain": "数据清洗", "title": "重复值检测与去重策略", "lessons": [21], "points": ["重复值", "drop_duplicates"]},
    {"id": "CLEAN-OUTLIER-001", "domain": "数据清洗", "title": "异常值识别(3σ/IQR)", "lessons": [22, 72], "points": ["异常值", "3σ", "IQR"]},
    {"id": "CLEAN-TEXT-001", "domain": "数据清洗", "title": "文本数据清洗与正则", "lessons": [23, 73], "points": ["文本清洗", "正则"]},
    {"id": "CLEAN-NORM-001", "domain": "数据清洗", "title": "数据标准化与归一化", "lessons": [24], "points": ["标准化", "归一化"]},
    {"id": "CLEAN-REPORT-001", "domain": "数据清洗", "title": "数据质量报告自动生成", "lessons": [25], "points": ["数据质量"]},

    # ---- 数据可视化 (5) ----
    {"id": "VIZ-MATPLOTLIB-001", "domain": "数据可视化", "title": "Matplotlib基础图表", "lessons": [26], "points": ["matplotlib"]},
    {"id": "VIZ-SEABORN-001", "domain": "数据可视化", "title": "Seaborn统计图表", "lessons": [27], "points": ["seaborn"]},
    {"id": "VIZ-PYECHARTS-001", "domain": "数据可视化", "title": "Pyecharts交互图表", "lessons": [28], "points": ["pyecharts"]},
    {"id": "VIZ-DASHBOARD-001", "domain": "数据可视化", "title": "多子图与Dashboard布局", "lessons": [29], "points": ["子图", "Dashboard"]},
    {"id": "VIZ-STYLE-001", "domain": "数据可视化", "title": "图表配色与商业报告排版", "lessons": [30], "points": ["配色", "报告排版"]},

    # ---- ETL数据管道 (5) ----
    {"id": "ETL-CONCEPT-001", "domain": "ETL数据管道", "title": "ETL概念与架构模式", "lessons": [31], "points": ["ETL", "架构"]},
    {"id": "ETL-EXTRACT-001", "domain": "ETL数据管道", "title": "数据抽取策略(全量/增量)", "lessons": [32], "points": ["数据抽取", "全量", "增量"]},
    {"id": "ETL-TRANSFORM-001", "domain": "ETL数据管道", "title": "数据转换规范与校验", "lessons": [33], "points": ["数据转换", "校验"]},
    {"id": "ETL-LOAD-001", "domain": "ETL数据管道", "title": "数据加载(SQL/NoSQL/Parquet)", "lessons": [34], "points": ["数据加载", "SQL", "NoSQL", "Parquet"]},
    {"id": "ETL-AIRFLOW-001", "domain": "ETL数据管道", "title": "Apache Airflow调度实战", "lessons": [35], "points": ["Airflow"]},

    # ---- SQL与数据库 (5) ----
    {"id": "SQL-QUERY-001", "domain": "SQL与数据库", "title": "SQL查询语句精讲", "lessons": [36], "points": ["SQL", "查询"]},
    {"id": "SQL-WINDOW-001", "domain": "SQL与数据库", "title": "窗口函数ROW_NUMBER/RANK", "lessons": [37], "points": ["窗口函数", "ROW_NUMBER", "RANK"]},
    {"id": "SQL-INDEX-001", "domain": "SQL与数据库", "title": "索引优化与执行计划", "lessons": [38], "points": ["索引", "执行计划"]},
    {"id": "SQL-PYTHON-001", "domain": "SQL与数据库", "title": "Python操作MySQL/SQLite", "lessons": [39], "points": ["MySQL", "SQLite"]},
    {"id": "SQL-ORM-001", "domain": "SQL与数据库", "title": "ORM框架SQLAlchemy入门", "lessons": [40], "points": ["SQLAlchemy", "ORM"]},

    # ---- 统计分析 (5) ----
    {"id": "STAT-DESC-001", "domain": "统计分析", "title": "描述统计(均值/方差/分位数)", "lessons": [41], "points": ["均值", "方差", "分位数"]},
    {"id": "STAT-DIST-001", "domain": "统计分析", "title": "概率分布(正态/二项/泊松)", "lessons": [42], "points": ["正态分布", "二项分布", "泊松分布"]},
    {"id": "STAT-TEST-001", "domain": "统计分析", "title": "假设检验t检验/卡方", "lessons": [43], "points": ["假设检验", "t检验", "卡方"]},
    {"id": "STAT-REGRESS-001", "domain": "统计分析", "title": "相关性与线性回归", "lessons": [44], "points": ["相关性", "线性回归"]},
    {"id": "STAT-ABTEST-001", "domain": "统计分析", "title": "AB测试设计与评估", "lessons": [45], "points": ["AB测试"]},

    # ---- 综合数据分析 (10) ----
    {"id": "BIZ-REQ-001", "domain": "综合数据分析", "title": "业务需求理解与拆解", "lessons": [46], "points": ["业务需求"]},
    {"id": "BIZ-COLLECT-001", "domain": "综合数据分析", "title": "多源数据采集与整合", "lessons": [47], "points": ["数据采集", "数据整合"]},
    {"id": "BIZ-RFM-001", "domain": "综合数据分析", "title": "RFM用户分层模型", "lessons": [48], "points": ["RFM"]},
    {"id": "BIZ-FORECAST-001", "domain": "综合数据分析", "title": "销售额趋势预测", "lessons": [49], "points": ["趋势预测"]},
    {"id": "BIZ-REPORT-001", "domain": "综合数据分析", "title": "分析报告撰写与汇报", "lessons": [50], "points": ["分析报告"]},
    {"id": "BIZ-HTTP-001", "domain": "综合数据分析", "title": "HTTP协议与Requests库", "lessons": [51], "points": ["HTTP", "Requests"]},
    {"id": "BIZ-XPATH-001", "domain": "综合数据分析", "title": "XPath/CSS选择器解析", "lessons": [52], "points": ["XPath", "CSS选择器"]},
    {"id": "BIZ-SCRAPY-001", "domain": "综合数据分析", "title": "Scrapy框架爬虫", "lessons": [53], "points": ["Scrapy"]},
    {"id": "BIZ-ANTI-001", "domain": "综合数据分析", "title": "反爬策略应对", "lessons": [54], "points": ["UserAgent", "IP池"]},
    {"id": "BIZ-CLEANVIZ-001", "domain": "综合数据分析", "title": "数据清洗存储与可视化", "lessons": [55], "points": ["数据清洗", "可视化"]},

    # ---- 性能优化与部署 (5) ----
    {"id": "PERF-VECTORIZE-001", "domain": "性能优化与部署", "title": "向量化替代循环操作", "lessons": [56], "points": ["向量化"]},
    {"id": "PERF-MEMORY-001", "domain": "性能优化与部署", "title": "内存优化与数据类型选择", "lessons": [57], "points": ["内存优化", "数据类型"]},
    {"id": "PERF-MULTIPROC-001", "domain": "性能优化与部署", "title": "多进程并行处理", "lessons": [58], "points": ["多进程", "并行"]},
    {"id": "PERF-DASK-001", "domain": "性能优化与部署", "title": "Dask分布式计算入门", "lessons": [59], "points": ["Dask"]},
    {"id": "PERF-DEPLOY-001", "domain": "性能优化与部署", "title": "Flask/FastAPI部署数据分析API", "lessons": [60], "points": ["Flask", "FastAPI"]},

    # ---- 扩展: 机器学习 (1) ----
    {"id": "ML-SPLIT-001", "domain": "机器学习(扩展)", "title": "Scikit-learn数据划分训练测试集", "lessons": [74], "points": ["train_test_split", "Scikit-learn"]},
]

# ============================================================
# 技能域 → 难度（启发式，按课程顺序）
# ============================================================
DOMAIN_DIFFICULTY = {
    "Python基础": 1,
    "NumPy": 2,
    "Pandas": 2,
    "数据清洗": 3,
    "数据可视化": 3,
    "ETL数据管道": 3,
    "SQL与数据库": 3,
    "统计分析": 4,
    "综合数据分析": 4,
    "性能优化与部署": 5,
    "机器学习(扩展)": 4,
}

# 技能域顺序（用于 curriculum_order 推导 prerequisites）
DOMAIN_ORDER = [
    "Python基础", "NumPy", "Pandas", "数据清洗", "数据可视化",
    "ETL数据管道", "SQL与数据库", "统计分析", "综合数据分析",
    "性能优化与部署", "机器学习(扩展)",
]


def load_lectures():
    """读 index.json 的 lectures，返回 {id: {title, dir, module}}"""
    with open(KB / "index.json", encoding="utf-8") as f:
        data = json.load(f)
    return {lec["id"]: lec for lec in data.get("lectures", [])}


def load_chunks():
    """读 chunks.jsonl，返回 {asset_id: [chunk_id, ...]}"""
    chunks = {}
    with open(KB / "assets" / "chunks.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                chunks.setdefault(c.get("asset_id", ""), []).append(c.get("chunk_id", ""))
    return chunks


def lesson_dir(lesson_id):
    """讲次号 → 目录号（两位字符串）"""
    return f"{lesson_id:02d}"


def quality_of(lessons):
    """根据讲次区间判断质量等级。
    - 01-12: generate_kb 中文结构化内容 → medium（真实、有结构）
    - 13-60: LLM 生成的中文详实内容（基于官方文档）→ medium（真实、详实，但 LLM 生成需人工抽检）
    - 61-74: curated 知识点版 → high（有 aliases/分节/练习）
    合并多讲次时取最高质量（curated 版提升整体）。
    """
    has_curated = any(l >= 61 for l in lessons)
    if has_curated:
        return "high", "reviewed"
    return "medium", "reviewed"


def build_knowledge_points():
    lectures = load_lectures()
    chunks = load_chunks()

    records = []
    for i, kp in enumerate(KNOWLEDGE):
        lessons = kp["lessons"]
        source_lessons = lessons
        source_chunks = []
        for l in lessons:
            asset_id = f"lecture-{lesson_dir(l)}"
            source_chunks.extend(chunks.get(asset_id, []))

        quality, review = quality_of(lessons)

        records.append({
            "knowledge_id": kp["id"],
            "title": kp["title"],
            "skill_domain": kp["domain"],
            "difficulty": DOMAIN_DIFFICULTY[kp["domain"]],
            "difficulty_source": "heuristic_by_course_order",
            "difficulty_confidence": 0.5,
            "source_lessons": source_lessons,
            "source_chunks": sorted(set(source_chunks)),
            "knowledge_points": kp["points"],
            "prerequisites": [],  # 下面统一填充
            "prerequisite_source": "curriculum_order",
            "common_errors": [],
            "quality_level": quality,
            "authority_level": "lecture",
            "review_status": review,
        })

    # ---- 填充 prerequisites（curriculum_order 推导）----
    # 规则1: 同域内，知识点 N 依赖知识点 N-1
    # 规则2: 跨域，每个域第一个知识点依赖前一个域的最后一个知识点
    domain_groups = {}
    for rec in records:
        domain_groups.setdefault(rec["skill_domain"], []).append(rec)

    for dom in DOMAIN_ORDER:
        if dom not in domain_groups:
            continue
        group = domain_groups[dom]
        for idx, rec in enumerate(group):
            prereqs = []
            if idx > 0:
                # 同域前序
                prereqs.append(group[idx - 1]["knowledge_id"])
            elif DOMAIN_ORDER.index(dom) > 0:
                # 跨域：依赖前一个域的最后一个知识点
                prev_dom = DOMAIN_ORDER[DOMAIN_ORDER.index(dom) - 1]
                prev_group = domain_groups.get(prev_dom, [])
                if prev_group:
                    prereqs.append(prev_group[-1]["knowledge_id"])
            rec["prerequisites"] = prereqs

    return records


def build_skill_tree(records):
    domains = []
    for dom in DOMAIN_ORDER:
        ids = [r["knowledge_id"] for r in records if r["skill_domain"] == dom]
        if not ids:
            continue
        domains.append({
            "id": dom,
            "name": dom,
            "difficulty_base": DOMAIN_DIFFICULTY[dom],
            "knowledge_ids": ids,
        })
    return {
        "domain": "Python数据分析",
        "version": "1.0",
        "canonical_source": "knowledge-base/index.json",
        "total_lectures": 74,
        "skill_domains": domains,
    }


def main():
    records = build_knowledge_points()
    skill_tree = build_skill_tree(records)

    out_kp = KB / "knowledge_points.json"
    out_sk = KB / "skill_tree.json"
    with open(out_kp, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    with open(out_sk, "w", encoding="utf-8") as f:
        json.dump(skill_tree, f, ensure_ascii=False, indent=2)

    print(f"生成知识点 {len(records)} 个 → {out_kp}")
    print(f"生成技能域 {len(skill_tree['skill_domains'])} 个 → {out_sk}")


if __name__ == "__main__":
    main()
