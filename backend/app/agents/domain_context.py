"""领域技能画像解析 —— 生成 Agent 个性化的统一输入源。

把「当前讲次属于哪个技能域」与「学习者在该域的分数」解析成一个 dict,
供 DocAgent / CodeAgent / QuizAgent / MindmapAgent / ReadingAgent / VideoAgent
统一消费,替换各自分散读取的老六维字段或空字段。

兜底链:evidence.skill_domain → profile.domain_skills → DB(get_profile) → 均值 → 50,
任何数据缺失都不崩、不落空。
"""
from typing import Any, Dict, List, Optional

from ..models.profile import DOMAIN_LABEL_TO_KEY, get_profile

# 分数分档阈值,与 CodeAgent / QuizAgent 既有阈值 35/70 一致
_BASIC_MAX = 35
_ADVANCED_MIN = 70


def resolve_domain_context(topic: str, profile: Optional[Dict[str, Any]],
                           sources: Optional[List[dict]] = None) -> Dict[str, Any]:
    """解析目标讲次的技能域 + 学习者在该域的掌握度。

    Args:
        topic: 讲次主题(当前仅作保留参数,域解析优先取 evidence 的 skill_domain)
        profile: 学习者画像 dict,含 domain_skills 时优先使用
        sources: RAG 检索出的 evidence 列表,每条含 skill_domain(中文)

    Returns:
        {"skill_domain": 中文域, "skill_key": 英文key, "score": int, "level": str}
    """
    profile = profile or {}

    # 1. 从 evidence 解析 skill_domain(中文) → skill_key(英文)
    skill_domain = None
    for s in (sources or []):
        d = (s or {}).get("skill_domain") or ""
        if d:
            skill_domain = d
            break
    skill_key = DOMAIN_LABEL_TO_KEY.get(skill_domain) if skill_domain else None

    # 2. 读分:profile.domain_skills → DB → 均值 → 50
    domain_skills = profile.get("domain_skills") or {}
    score = domain_skills.get(skill_key) if skill_key else None

    if score is None and profile.get("user_id"):
        try:
            db_skills = get_profile(profile["user_id"]).domain_skills or {}
            domain_skills = db_skills
            score = db_skills.get(skill_key) if skill_key else None
        except Exception:
            pass

    if score is None:
        vals = [v for v in domain_skills.values() if isinstance(v, (int, float))]
        score = round(sum(vals) / len(vals)) if vals else 50

    score = int(score)

    # 3. 分档
    if score < _BASIC_MAX:
        level = "basic"
    elif score < _ADVANCED_MIN:
        level = "intermediate"
    else:
        level = "advanced"

    return {
        "skill_domain": skill_domain,
        "skill_key": skill_key,
        "score": score,
        "level": level,
    }
