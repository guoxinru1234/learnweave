#!/usr/bin/env python3
"""P6: 比赛指标评测脚本。

评估 4 项指标（对每个学习者）：
  1. 幻觉率           —— 生成内容 vs RAG Evidence（无依据事实占比）
  2. 知识覆盖率       —— 目标知识点 vs 生成内容（标签覆盖比例）
  3. 画像—难度适配    —— 学生掌握度 vs 资源难度（匹配率）
  4. 动态反馈有效率   —— 发现弱项后是否真的改变学习路径

用法:
  python scripts/evaluate_competition_metrics.py
"""
import sys
import json
import asyncio
import re
from pathlib import Path

# 把 backend 目录加入 sys.path，以便 import 后端 agent
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.agents.knowledge_agent import KnowledgeRetrievalAgent
from app.agents.doc_agent import DocAgent
from app.agents.audit_agent import AuditAgent
from app.agents.assessment_agent import AssessmentAgent
from app.agents.path_planner_agent import PathPlannerAgent
from app.models.profile import (
    set_initial_domain_skills, get_profile, DOMAIN_SKILL_LABELS,
)
from app.core.event_bus import event_bus


# 3 个不同学习者（领域技能画像，与 P1 的 10 技能域一致）
LEARNERS = {
    "学生A（基础薄弱）": {
        "python_basic": 40, "pandas": 30, "statistics": 20,
    },
    "学生B（Python较强但数据分析弱）": {
        "python_basic": 90, "pandas": 45, "data_cleaning": 35, "statistics": 30,
    },
    "学生C（数据分析较强）": {
        "python_basic": 90, "pandas": 85, "data_cleaning": 80,
        "visualization": 85, "statistics": 75,
    },
}


def hallucination_rate(issues: list) -> float:
    """幻觉率：AuditAgent 判定为"无来源/幻觉/冲突"的 issue 占比。"""
    if not issues:
        return 0.0
    hallucination_kw = ["无来源", "幻觉", "未支持", "未引用", "冲突", "无依据", "编造"]
    hallucination_count = sum(
        1 for iss in issues
        if any(kw in (iss.get("description") or "") for kw in hallucination_kw)
    )
    return hallucination_count / len(issues)


def knowledge_coverage(knowledge_points: list, generated_content: str) -> float:
    """知识覆盖率：目标知识点标签在生成内容中出现的比例。"""
    if not knowledge_points:
        return 1.0
    content_lower = (generated_content or "").lower()
    covered = sum(1 for p in knowledge_points if str(p).lower() in content_lower)
    return covered / len(knowledge_points)


def difficulty_match(student_score: int, difficulty: int) -> bool:
    """难度适配：学生掌握度 vs 资源难度是否匹配。"""
    if student_score < 50:
        return difficulty <= 2      # 薄弱 → 低难度
    elif student_score > 80:
        return difficulty >= 4      # 强 → 高难度
    return 2 <= difficulty <= 4     # 中等 → 中难度


def score_to_foundation(score: int) -> str:
    """掌握度分数 → 基础等级（供 DocAgent 调整难度）。"""
    if score < 40:
        return "零基础"
    elif score < 60:
        return "入门"
    elif score < 80:
        return "中等"
    return "良好"


def recommended_difficulty(score: int) -> int:
    """掌握度分数 → 推荐资源难度（1-5）。"""
    if score < 40:
        return 1
    elif score < 60:
        return 2
    elif score < 80:
        return 3
    return 4


async def evaluate_learner(name: str, skills: dict, user_id: int) -> dict:
    """评测单个学习者，返回 4 项指标 + 差异化信息。"""
    print(f"\n{'=' * 60}")
    print(f"评测 {name}")
    print(f"画像: {skills}")
    print('=' * 60)

    # 1. 设置画像 + 识别最弱技能
    set_initial_domain_skills(user_id, skills)
    weak_skill_key = min(skills, key=skills.get)
    weak_skill_cn = DOMAIN_SKILL_LABELS.get(weak_skill_key, weak_skill_key)
    weak_score = skills[weak_skill_key]
    print(f"[1] 最弱技能: {weak_skill_cn}（{weak_score}分）")

    # 2. 检索知识点 + evidence
    ka = KnowledgeRetrievalAgent()
    kps = ka.retrieve_knowledge_points(weak_skill_cn, skill_domain=weak_skill_cn, top_k=1)
    kp = kps[0] if kps else None
    evidence = ka.retrieve(weak_skill_cn, top_k=3)
    print(f"[2] 目标知识点: {kp['knowledge_id'] if kp else '未找到'} "
          f"difficulty={kp.get('difficulty') if kp else '?'}")
    print(f"    检索 evidence {len(evidence)} 条")

    # 3. 生成资源（带画像 + 知识点 + evidence；foundation 由掌握度推导，驱动难度）
    foundation = score_to_foundation(weak_score)
    profile_with_foundation = {**skills, "foundation": foundation}
    doc = DocAgent()
    state = {
        "lecture_topic": weak_skill_cn,
        "skill_domain": weak_skill_cn,
        "profile": profile_with_foundation,
        "mode": "study",
        "knowledge_context": {"sources": evidence, "knowledge_points": kps, "topic": weak_skill_cn},
    }
    doc_result = await doc.execute(state)
    content = doc_result.get("lecture_doc", {}).get("content", "")
    print(f"[3] 生成资源 {len(content)} 字符")

    # 4. 审核
    audit = AuditAgent()
    audit_state = {**state, "lecture_doc": doc_result.get("lecture_doc", {}),
                   "code_example": {}, "mindmap": {}, "quiz": {}, "extended_reading": {}}
    audit_result = await audit.execute(audit_state)
    report = audit_result.get("audit_report", {})
    issues = report.get("issues", [])
    print(f"[4] 审核 confidence={report.get('overall_confidence')}%, issues={len(issues)}")

    # 5. 计算指标
    hallu = hallucination_rate(issues)
    target_points = kp.get("knowledge_points", []) if kp else []
    coverage = knowledge_coverage(target_points, content)
    diff = kp.get("difficulty", 3) if kp else 3
    diff_ok = difficulty_match(weak_score, diff)

    print(f"[5] 指标:")
    print(f"    幻觉率: {hallu:.0%}（{len(issues)} issues 中无依据类占比）")
    print(f"    知识覆盖率: {coverage:.0%}（{target_points}）")
    print(f"    难度适配: {'匹配' if diff_ok else '不匹配'}（学生{weak_score}分 vs 静态难度{diff}）")
    print(f"    推荐难度: {recommended_difficulty(weak_score)}（由掌握度 {weak_score} 推导，foundation={foundation}）")

    return {
        "learner": name,
        "weak_skill": weak_skill_cn,
        "weak_score": weak_score,
        "foundation": foundation,
        "knowledge_id": kp["knowledge_id"] if kp else None,
        "difficulty": diff,
        "recommended_difficulty": recommended_difficulty(weak_score),
        "content_length": len(content),
        "audit_confidence": report.get("overall_confidence", 0),
        "hallucination_rate": round(hallu, 3),
        "knowledge_coverage": round(coverage, 3),
        "difficulty_match": diff_ok,
    }


async def dynamic_feedback_efficiency(user_id: int, weak_skill_cn: str) -> bool:
    """动态反馈有效率：模拟弱项检测后，PathPlanner 是否真的改变路径指向弱项。"""
    generated_plans = []
    async def on_plan(event):
        generated_plans.append(event.data.get("plan", {}))
    event_bus.subscribe("PLAN_GENERATED", on_plan)

    assess = AssessmentAgent()
    planner = PathPlannerAgent()

    # 模拟一次弱项 Quiz 失败
    await event_bus.publish("QUIZ_SUBMITTED", {
        "topic": weak_skill_cn, "correct": False, "difficulty": "medium",
        "user_id": user_id, "score": 40, "total": 100,
    })

    # 检查 PathPlanner 是否推荐了弱项知识点
    if generated_plans:
        plan = generated_plans[-1]
        return bool(plan.get("knowledge_id")) and plan.get("action") == "专项训练"
    return False


async def main():
    print("#" * 70)
    print("# P6 比赛指标评测")
    print("#" * 70)

    results = []
    for idx, (name, skills) in enumerate(LEARNERS.items(), start=100):
        r = await evaluate_learner(name, skills, idx)
        # 动态反馈有效率
        fb_ok = await dynamic_feedback_efficiency(idx, r["weak_skill"])
        r["dynamic_feedback"] = fb_ok
        print(f"    动态反馈有效率: {'有效' if fb_ok else '无效'}（弱项检测后路径指向专项训练）")
        results.append(r)

    # 汇总表
    print(f"\n{'=' * 70}")
    print("汇总对比（3 学习者差异化）")
    print('=' * 70)
    print(f"{'学习者':<22} {'最弱技能':<8} {'掌握度':<5} {'推荐难度':<7} {'覆盖率':<6} {'难度适配':<6} {'动态反馈':<6}")
    for r in results:
        print(f"{r['learner']:<22} {r['weak_skill']:<8} {r['weak_score']:<5} "
              f"{r['recommended_difficulty']:<7} {r['knowledge_coverage']:.0%} "
              f"{'OK' if r['difficulty_match'] else 'X':<6} {'OK' if r['dynamic_feedback'] else 'X':<6}")

    # 差异化断言
    weak_skills = {r["weak_skill"] for r in results}
    recommended_difficulties = {r["recommended_difficulty"] for r in results}
    foundations = {r["foundation"] for r in results}
    print(f"\n差异化验证:")
    print(f"  最弱技能集合: {weak_skills}")
    print(f"  推荐难度集合: {recommended_difficulties}（{'不同' if len(recommended_difficulties) > 1 else '相同'}）")
    print(f"  foundation 集合: {foundations}（{'不同' if len(foundations) > 1 else '相同'}）")

    # 保存结果
    out = Path(__file__).resolve().parent.parent / "backend" / "data" / "competition_metrics.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    asyncio.run(main())
