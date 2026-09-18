#!/usr/bin/env python3
"""知识库质量检查（P1.9）。

检查项:
  - knowledge_id 重复
  - source_lesson 不存在（不在 index.json lectures 中）
  - source_chunk 不存在（不在 chunks.jsonl 中）
  - prerequisite 悬空引用（指向不存在的 knowledge_id）
  - difficulty 非法（不在 1-5 范围）
  - knowledge_points 为空
  - 无来源知识点（source_lessons 为空）

用法:
  python scripts/evaluate_knowledge_base.py
"""
import json
import sys
from pathlib import Path

KB = Path(__file__).resolve().parent.parent / "knowledge-base"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    kp_path = KB / "knowledge_points.json"
    sk_path = KB / "skill_tree.json"
    idx_path = KB / "index.json"
    chunks_path = KB / "assets" / "chunks.jsonl"

    if not kp_path.exists():
        print("ERROR: knowledge_points.json 不存在，请先运行 scripts/build_knowledge_base.py")
        sys.exit(1)

    points = load_json(kp_path)
    index = load_json(idx_path)
    valid_lessons = {lec["id"] for lec in index.get("lectures", [])}

    # 收集所有合法 chunk_id
    valid_chunks = set()
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                valid_chunks.add(json.loads(line).get("chunk_id", ""))

    valid_ids = {p["knowledge_id"] for p in points}

    # ---- 统计 ----
    dup_ids = []
    seen_ids = set()
    for p in points:
        kid = p["knowledge_id"]
        if kid in seen_ids:
            dup_ids.append(kid)
        seen_ids.add(kid)

    missing_source = []
    missing_chunk = []
    broken_prereq = []
    illegal_difficulty = []
    empty_points = []
    no_source = []

    for p in points:
        # source_lesson 不存在
        for l in p.get("source_lessons", []):
            if l not in valid_lessons:
                missing_source.append((p["knowledge_id"], l))
        # source_chunk 不存在
        for c in p.get("source_chunks", []):
            if c not in valid_chunks:
                missing_chunk.append((p["knowledge_id"], c))
        # prerequisite 悬空
        for pre in p.get("prerequisites", []):
            if pre not in valid_ids:
                broken_prereq.append((p["knowledge_id"], pre))
        # difficulty 非法
        d = p.get("difficulty")
        if not isinstance(d, int) or d < 1 or d > 5:
            illegal_difficulty.append(p["knowledge_id"])
        # knowledge_points 为空
        if not p.get("knowledge_points"):
            empty_points.append(p["knowledge_id"])
        # 无来源
        if not p.get("source_lessons"):
            no_source.append(p["knowledge_id"])

    # ---- 输出 ----
    print("=" * 50)
    print("Knowledge Base Validation")
    print("=" * 50)
    print(f"Total knowledge points: {len(points)}")
    print()
    print(f"Duplicate IDs:          {len(dup_ids)}")
    print(f"Missing source lesson:  {len(missing_source)}")
    print(f"Missing source chunk:   {len(missing_chunk)}")
    print(f"Broken prerequisites:   {len(broken_prereq)}")
    print(f"Illegal difficulty:     {len(illegal_difficulty)}")
    print(f"Empty knowledge_points: {len(empty_points)}")
    print(f"No source lessons:      {len(no_source)}")
    print()

    # 质量分布
    quality_dist = {}
    for p in points:
        q = p.get("quality_level", "unknown")
        quality_dist[q] = quality_dist.get(q, 0) + 1
    print("Quality distribution:")
    for q, n in sorted(quality_dist.items()):
        print(f"  {q}: {n}")
    print()

    # 技能域分布
    domain_dist = {}
    for p in points:
        d = p.get("skill_domain", "unknown")
        domain_dist[d] = domain_dist.get(d, 0) + 1
    print("Skill domain distribution:")
    for d, n in domain_dist.items():
        print(f"  {d}: {n}")

    print()
    valid_count = len(points) - len(set(dup_ids)) - len(set(k for k, _ in missing_source)) - len(set(k for k, _ in broken_prereq)) - len(illegal_difficulty) - len(no_source)
    invalid = len(points) - valid_count
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid}")

    # 明细（若有问题）
    if dup_ids:
        print(f"\n[重复 ID] {dup_ids}")
    if missing_source:
        print(f"\n[缺失来源讲次] {missing_source[:10]}")
    if missing_chunk:
        print(f"\n[缺失 chunk] {missing_chunk[:10]}")
    if broken_prereq:
        print(f"\n[悬空 prerequisite] {broken_prereq[:10]}")
    if illegal_difficulty:
        print(f"\n[非法难度] {illegal_difficulty}")
    if empty_points:
        print(f"\n[空 knowledge_points] {empty_points}")
    if no_source:
        print(f"\n[无来源] {no_source}")

    # 退出码：有硬错误则非 0
    hard_errors = dup_ids or missing_source or broken_prereq or illegal_difficulty or no_source
    sys.exit(1 if hard_errors else 0)


if __name__ == "__main__":
    main()
