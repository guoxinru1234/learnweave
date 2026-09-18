"""把「Python环境搭建与Jupyter入门」挂进知识库索引 + 知识点(第0讲, 00/)。"""
import json
import os

KB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge-base")

# 1. index.json —— 在 lectures 数组最前插入第0讲
idx_path = os.path.join(KB, "index.json")
idx = json.load(open(idx_path, encoding="utf-8"))
new_lecture = {"id": 0, "title": "Python环境搭建与Jupyter入门", "dir": "00",
               "file": "lecture.md", "module": "Python基础速成"}
lectures = idx.get("lectures", [])
if not any(l.get("id") == 0 for l in lectures):
    idx["lectures"] = [new_lecture] + lectures
    idx["total_lectures"] = len(idx["lectures"])
    # modules(展示用)也同步:第一个模块标题列表最前插入
    mods = idx.get("modules", [])
    if mods and isinstance(mods[0], list) and len(mods[0]) >= 2:
        mods[0][1] = ["Python环境搭建与Jupyter入门"] + mods[0][1]
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"index.json: 已加第0讲, total_lectures = {idx['total_lectures']}")
else:
    print("index.json: 第0讲已存在")

# 2. knowledge_points.json —— 最前插入 PY-ENV-001
kp_path = os.path.join(KB, "knowledge_points.json")
kps = json.load(open(kp_path, encoding="utf-8"))
new_kp = {
    "knowledge_id": "PY-ENV-001",
    "title": "Python环境搭建与Jupyter入门",
    "skill_domain": "Python基础",
    "difficulty": 1,
    "difficulty_source": "heuristic_by_course_order",
    "difficulty_confidence": 0.5,
    "source_lessons": [0],
    "source_chunks": ["00-000"],
    "knowledge_points": ["Python安装", "虚拟环境", "pip", "Jupyter", "环境变量PATH"],
    "prerequisites": [],
    "prerequisite_source": "curriculum_order",
    "common_errors": [],
    "quality_level": "high",
    "authority_level": "lecture",
    "review_status": "reviewed",
}
if not any(k.get("knowledge_id") == "PY-ENV-001" for k in kps):
    kps.insert(0, new_kp)
    json.dump(kps, open(kp_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("knowledge_points.json: 已加 PY-ENV-001")
else:
    print("knowledge_points.json: PY-ENV-001 已存在")
