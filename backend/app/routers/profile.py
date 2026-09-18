import json
import re
from fastapi import APIRouter, HTTPException, Depends
from ..core.deps import get_current_user_id
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from ..models.profile import get_profile, save_profile, set_initial_domain_skills
from ..agents.profile_agent import get_profile_agent
from ..core.llm import LLMError, LLMAuthError, LLMTimeoutError, get_llm_client

router = APIRouter(prefix="/api/profile", tags=["profile"])
_PATH_CACHE: dict[str, dict] = {}


class ChatRequest(BaseModel):
    user_id: int = 1
    message: str


class ChatResponse(BaseModel):
    message: str
    profile: Dict[str, Any]
    updates: List[Dict[str, Any]]
    dialogue_step: int
    completed: bool
    completion_percentage: int
    descriptions: Dict[str, str]


class RecommendRequest(BaseModel):
    user_id: int = 1
    weak_dimensions: List[List[Any]] = []   # [[name, score], ...]
    strong_dimensions: List[List[Any]] = []  # [[name, score], ...]


class RecommendedLecture(BaseModel):
    lecture_id: int
    title: str
    reason: str
    priority: str  # "high" | "medium"


class RecommendResponse(BaseModel):
    recommendations: List[RecommendedLecture]
    summary: str


class SetDomainSkillsRequest(BaseModel):
    user_id: int = 1
    skills: Dict[str, int] = {}   # {skill_key: 0-100}


@router.get("")
async def get_profile_data(user_id: int = Depends(get_current_user_id)):
    """获取画像数据；首次访问时由 LLM 生成开场白"""
    profile = get_profile(user_id)

    if len(profile.dialogue_history) == 0:
        agent = get_profile_agent()
        try:
            result = await agent.start_conversation(user_id)
        except LLMAuthError:
            # LLM 未配置时使用硬编码问候语作为后备
            from ..models.profile import LearnerProfile
            greeting = "你好！我是 LearnWeave 的学习助手 🤗 很高兴认识你！先简单了解一下——你的专业和年级是什么？想学哪方面的内容？"
            profile.dialogue_history.append({"role": "assistant", "content": greeting})
            profile.dialogue_step = 0
            save_profile(profile)
        except LLMError:
            greeting = "你好！我是 LearnWeave 的学习助手 🤗 很高兴认识你！先简单了解一下——你的专业和年级是什么？想学哪方面的内容？"
            profile.dialogue_history.append({"role": "assistant", "content": greeting})
            profile.dialogue_step = 0
            save_profile(profile)

        profile = get_profile(user_id)

    return {
        "major_background": profile.major_background,
        "theoretical_basis": profile.theoretical_basis,
        "coding_ability": profile.coding_ability,
        "practical_ops": profile.practical_ops,
        "troubleshooting": profile.troubleshooting,
        "data_thinking": profile.data_thinking,
        "self_learning": profile.self_learning,
        "overall_score": profile.overall_score,
        "weak_dimensions": profile.weak_dimensions,
        "strong_dimensions": profile.strong_dimensions,
        "domain_skills": profile.domain_skills,
        "domain_weak_skills": profile.domain_weak_skills,
        "domain_strong_skills": profile.domain_strong_skills,
        "theory_description": profile.theory_description,
        "coding_description": profile.coding_description,
        "practice_description": profile.practice_description,
        "debug_description": profile.debug_description,
        "data_description": profile.data_description,
        "self_learning_description": profile.self_learning_description,
        "cognitive_style": profile.cognitive_style,
        "learning_pace": profile.learning_pace,
        "learning_motivation": profile.learning_motivation,
        "dialogue_step": profile.dialogue_step,
        "dialogue_completed": profile.dialogue_completed,
        "completion_percentage": profile.completion_percentage,
        # Return the complete profile interview so the learner can review how
        # each score and recommendation was established.  The UI already
        # virtualizes/scrolls this panel, so truncating here only hid history.
        "dialogue_history": profile.dialogue_history,
    }


@router.post("/domain-skills")
async def set_domain_skills(request: SetDomainSkillsRequest):
    """设置领域技能画像(演示用画像预设切换:零基础/中等/进阶)。"""
    raise HTTPException(status_code=410, detail="Profile scores must come from human dialogue answers.")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_profile_agent(request: ChatRequest):
    """处理学生回答，LLM 自主驱动对话"""
    try:
        agent = get_profile_agent()
        result = await agent.process_answer(request.user_id, request.message)
        return ChatResponse(**result)
    except LLMAuthError as e:
        raise HTTPException(status_code=503, detail=f"LLM 服务未配置: {str(e)}")
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=f"LLM 服务超时，请稍后重试")
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"LLM 服务错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像智能体错误: {str(e)}")


def _extract_paths_json(raw: str) -> dict | None:
    """从 LLM 回复中稳健提取 paths JSON(容错:去代码块、截取花括号、剥尾随逗号)。"""
    if not raw:
        return None
    text = raw
    # 1. 去掉 ```json ``` 代码块
    m = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if m:
        text = m.group(1).strip()
    # 2. 截取第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start < 0 or end <= start:
        return None
    text = text[start:end + 1]
    # 3. 去掉 LLM 常见的尾随逗号
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    # 4. 解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@router.get("/paths")
async def get_path_recommendations(user_id: int = Depends(get_current_user_id)):
    """根据领域技能画像，为每个学生生成3条个性化学习路径。

    每条路径对应补弱/强化/均衡三种策略，基于 Python 数据分析领域技能（domain_skills）。
    """
    from ..models.profile import DOMAIN_SKILL_LABELS
    profile = get_profile(user_id)
    skills = profile.domain_skills or {}
    # Stable per-account/profile snapshot: refreshing either page must not
    # trigger a new stochastic LLM response.
    import hashlib
    profile_key = hashlib.sha256(json.dumps(skills, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()[:16]
    cache_key = f"{user_id}:{profile_key}"
    if cache_key in _PATH_CACHE:
        return _PATH_CACHE[cache_key]
    valid = {k: v for k, v in skills.items() if v > 0}

    if len(valid) < 2:
        return {"paths": [], "note": "请先完成领域技能评估（至少2个技能）"}

    dim_labels = {k: DOMAIN_SKILL_LABELS.get(k, k) for k in valid}
    avg = sum(valid.values()) // len(valid)
    # Persist a deterministic, profile-derived lecture order so profile and
    # learning-space pages always render the same path for the same account.
    try:
        from ..core.database import get_connection
        conn = get_connection()
        rows = conn.execute("SELECT id FROM lectures ORDER BY id").fetchall()
        all_nums = [int(r[0]) for r in rows]
    except Exception:
        all_nums = list(range(1, 25))
    if skills.get('python_basic', 0) >= 50:
        all_nums = [n for n in all_nums if n != 1]
    sorted_skills = sorted(valid.items(), key=lambda x: x[1])
    low = [(dim_labels[k], v) for k, v in sorted_skills[:2]]
    high = [(dim_labels[k], v) for k, v in sorted_skills[-2:]]
    # Build genuinely different routes from the learner's weakest/strongest
    # dimensions.  The previous modulo ordering produced three look-alike
    # paths and ignored the profile.
    dim_lectures = {
        'python_basic':[1,2,3,4], 'numpy':[5,6,7,8],
        'pandas':[9,10,11,12], 'data_cleaning':[10,11,12],
        'visualization':[13,14,15,16], 'etl':[17,18,19],
        'sql':[17,18,20], 'statistics':[8,12,21],
        'comprehensive_analysis':[19,21,22,23], 'performance':[20,22,23,24],
    }
    def focus_nums(items):
        out=[]
        for key,_ in items:
            for n in dim_lectures.get(key,[]):
                if n in all_nums and n not in out: out.append(n)
        return out
    weak_focus, strong_focus = focus_nums(sorted_skills[:3]), focus_nums(sorted_skills[-3:])
    balanced = sorted(all_nums, key=lambda n: (abs((n % 10) - (avg % 10)), n))
    # Advanced learners should not be forced through mastered lectures. Keep
    # only topics mapped to below-threshold dimensions; retain a short
    # challenge set for the strongest route.
    if avg >= 75:
        # High-mastery learners skip mastered content. Keep only a compact
        # remediation set (<75) plus a small, advanced challenge set.
        weak_active = focus_nums([(k, v) for k, v in sorted_skills if v < 75][:3])
        challenge_active = focus_nums([(k, v) for k, v in sorted_skills if v >= 75][-2:])
        active_nums = list(dict.fromkeys(weak_active + challenge_active))
        if not active_nums:
            active_nums = all_nums[-4:]
    else:
        active_nums = all_nums
    if avg >= 75:
        # C/high mastery: concise routes with only remediation and challenge.
        lecture_orders = {
            'path_1': list(dict.fromkeys(weak_focus))[:5] or active_nums[:3],
            'path_2': list(dict.fromkeys(challenge_active))[:5] or active_nums[-3:],
            # Comprehensive transfer route is intentionally longer than the
            # two focused routes, while still excluding mastered intro items.
            'path_3': list(dict.fromkeys([10] + [n for n in balanced if n in active_nums]))[:12],
        }
    elif avg >= 45:
        # B/intermediate mastery: broader coverage and more guided practice.
        lecture_orders = {
            'path_1': list(dict.fromkeys(weak_focus + [n for n in all_nums if n not in weak_focus]))[:14],
            'path_2': list(dict.fromkeys(strong_focus + [n for n in reversed(all_nums) if n not in strong_focus]))[:12],
            # Intermediate learners need the broadest, end-to-end route.
            # Keep the broad route within the 24-lecture course catalog so
            # both profile and learning-space pages can render every item.
            'path_3': list(dict.fromkeys([10] + [n for n in balanced if n <= 24]))[:18],
        }
    else:
        # A/foundational mastery: near-complete scaffolded route.
        lecture_orders = {
            'path_1': list(dict.fromkeys(weak_focus + all_nums))[:20],
            'path_2': list(dict.fromkeys(strong_focus + all_nums))[:16],
            'path_3': balanced,
        }

    # LLM 基于领域技能生成3条路径
    dim_lines = "\n".join(f"- {dim_labels[k]}：{v}分" for k, v in sorted_skills)
    prompt = f"""你是一位资深数据分析教育顾问。根据以下学生的领域技能画像，设计3条不同的学习路径。

【领域技能画像】（Python 数据分析方向，满分100）
{dim_lines}

综合均分：{avg}分
最弱技能：{', '.join(f'{name}{score}分' for name, score in low)}
最强技能：{', '.join(f'{name}{score}分' for name, score in high)}

3条路径必须分别对应3种不同策略：

1. 补弱路线 — 哪里弱就重点攻哪里（针对最弱的数据分析技能）
2. 强化路线 — 把优势发挥到极致（针对最强的技能）
3. 均衡路线 — 齐头并进

每条路径输出4个字段：
- label：路径名称（要具体有画面感，如"Pandas聚合专项突破"而不是"补弱路线"）
- reason：给学生的推荐理由（2-3句话，引用分数）
- strategy：给学习者的学习方案（从"怎么学"的角度写，写明：①先学什么 ②怎么学 ③练什么巩固）
- focus：这条路径重点覆盖的技能域（中文，2-4个，必须从上面【领域技能画像】的维度名里选，如"ETL数据管道"、"统计分析"）

大多数人最需要补弱，补弱路线默认recommended:true。

输出纯JSON：
{{"paths":[{{"id":"path_1","icon":"🔧","label":"具体的补弱路径名","recommended":true,"reason":"给学生的理由","strategy":"给学习者的学习方案","focus":["ETL数据管道","综合数据分析"]}},{{"id":"path_2","icon":"⚡","label":"具体的强化路径名","recommended":false,"reason":"给学生的理由","strategy":"给学习者的学习方案","focus":["数据可视化","统计分析"]}},{{"id":"path_3","icon":"⚖️","label":"具体的均衡路径名","recommended":false,"reason":"给学生的理由","strategy":"给学习者的学习方案","focus":["Python基础","Pandas"]}}]}}"""

    try:
        llm = get_llm_client()
        raw = await llm.chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=1200)
        data = _extract_paths_json(raw)
        if data and data.get("paths"):
            # 覆盖 label 为确定性名称,保证学情画像与学习空间两页一致
            weak_name = low[0][0]
            strong_name = high[-1][0]
            for p in data["paths"]:
                pid = p.get("id")
                if pid == "path_1":
                    p["label"] = f"{weak_name}专项突破"
                elif pid == "path_2":
                    p["label"] = f"{strong_name}深度拓展"
                elif pid == "path_3":
                    p["label"] = "均衡系统推进"
                p["lecture_order"] = lecture_orders.get(pid, all_nums)
                p["lecture_ids"] = p["lecture_order"]
                # Ensure each route has distinct, profile-driven focus and strategy.
                if pid == "path_1":
                    p["recommended"] = True
                    p["focus"] = [n for n, _ in low]
                    p["strategy"] = "先补齐最弱维度，再通过分层练习和错题复盘巩固"
                elif pid == "path_2":
                    p["recommended"] = False
                    p["focus"] = [n for n, _ in high]
                    p["strategy"] = "围绕优势能力进入复杂案例、性能分析与工程实践"
                elif pid == "path_3":
                    p["recommended"] = False
                    p["focus"] = [dim_labels[k] for k, _ in sorted_skills]
                    p["strategy"] = "按项目阶段串联多领域知识，完成端到端综合项目"
            _PATH_CACHE[cache_key] = data
            return data
    except Exception as e:
        print(f"[PathRec] LLM 生成失败: {e}")

    # 最终回退：用最弱/最强领域技能生成
    weak_name, weak_score = low[0]
    strong_name, strong_score = high[-1]
    result = {
        "paths": [
            {"id": "path_1", "icon": "🔧", "label": f"{weak_name}专项突破",
             "recommended": True,
             "reason": f"你{weak_name}{weak_score}分是短板——这条路在{weak_name}相关讲次投入更多时间，用类比→理解→定义→练习四步法，把拖后腿的先补上来。",
             "strategy": f"补弱方案：你{weak_name}是短板。建议①先看讲义的类比和概念 ②跟着代码示例逐行敲 ③做5道从基础到进阶的练习题巩固。",
             "focus": [n for n, _ in low]},
            {"id": "path_2", "icon": "⚡", "label": f"{strong_name}深度拓展",
             "recommended": False,
             "reason": f"你{strong_name}{strong_score}分是强项——这条路在优势方向深入拓展，引入源码分析和进阶内容，把擅长的做到极致。",
             "strategy": f"强化方案：你{strong_name}是强项。建议①读源码和进阶资料 ②挑战性能优化 ③做工业级项目实战。",
             "focus": [n for n, _ in high]},
            {"id": "path_3", "icon": "⚖️", "label": "均衡系统推进",
             "recommended": False,
             "reason": f"综合{avg}分，按课程大纲稳步推进，每讲理论与实践各半，不偏不倚齐头并进。",
             "strategy": f"均衡方案：按课程大纲推进。每讲①先学概念 ②再动手写代码 ③做适中难度练习题。",
             "focus": [dim_labels[k] for k in list(valid)[:3]]},
        ]
    }
    for p in result['paths']:
        p['lecture_order'] = lecture_orders.get(p['id'], all_nums)
        p['lecture_ids'] = p['lecture_order']
    _PATH_CACHE[cache_key] = result
    return result


@router.post("/reset")
async def reset_profile(user_id: int = Depends(get_current_user_id)):
    """重置画像（删除数据库记录）"""
    from ..models.profile import _get_conn
    conn = _get_conn()
    conn.execute("DELETE FROM learner_profiles WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "画像已重置"}


# ========== 维度 → 讲次映射 ==========

DIMENSION_LECTURE_MAP: Dict[str, list] = {
    "理论基础": {
        "lecture_ids": [1, 2, 5, 6, 7, 8],
        "label": "理论基础",
        "reason_template": "夯实{name}基础，系统学习核心概念与原理",
    },
    "编程能力": {
        "lecture_ids": [1, 2, 5, 6, 7, 9],
        "label": "编程能力",
        "reason_template": "通过{name}强化编程实战，提升代码能力",
    },
    "实践操作": {
        "lecture_ids": [3, 4, 5, 10],
        "label": "实践操作",
        "reason_template": "结合{name}动手实践，掌握环境搭建与工具使用",
    },
    "问题排查": {
        "lecture_ids": [7, 8, 10, 12],
        "label": "问题排查",
        "reason_template": "学习{name}中的排错技巧，培养系统调试思维",
    },
    "数据思维": {
        "lecture_ids": [9, 10, 12],
        "label": "数据思维",
        "reason_template": "通过{name}培养数据分析流程和建模思维",
    },
    "自学能力": {
        "lecture_ids": [1, 2, 3, 5, 7, 9, 10, 12],
        "label": "自学能力",
        "reason_template": "结合{name}锻炼自主查阅文档和独立解决问题的能力",
    },
}

LECTURE_TOPICS: Dict[int, str] = {
    1: "Python环境搭建与Jupyter入门",
    2: "变量、数据类型与运算符",
    3: "条件判断与循环控制",
    4: "函数定义与模块化编程",
    5: "NumPy数组创建与索引",
    6: "数组运算与广播机制",
    7: "线性代数与矩阵运算",
    8: "随机数与统计函数",
    9: "Series与DataFrame基础",
    10: "数据筛选与条件过滤",
    11: "数据合并：merge/concat/join",
    12: "数据透视表与分组聚合",
}


def _build_recommendations(weak_dims: list, strong_dims: list) -> tuple[list[dict], str]:
    """根据薄弱/优势维度构建推荐讲次"""
    recommendations: list[dict] = []
    seen_ids: set = set()

    # 取最薄弱的 2 个维度重点推荐
    for dim_name, score in weak_dims[:2]:
        mapping = DIMENSION_LECTURE_MAP.get(dim_name)
        if not mapping:
            continue
        for lid in mapping["lecture_ids"]:
            if lid not in seen_ids:
                lecture_title = LECTURE_TOPICS.get(lid, f"第{lid}讲")
                reason = mapping["reason_template"].format(name=lecture_title)
                recommendations.append({
                    "lecture_id": lid,
                    "title": lecture_title,
                    "reason": reason,
                    "priority": "high" if score < 60 else "medium",
                })
                seen_ids.add(lid)

    # 如果推荐太少，补充一些基础讲次
    if len(recommendations) < 3:
        for lid in [1, 2, 3, 5]:
            if lid not in seen_ids:
                recommendations.append({
                    "lecture_id": lid,
                    "title": LECTURE_TOPICS.get(lid, f"第{lid}讲"),
                    "reason": f"补充学习{LECTURE_TOPICS.get(lid, f'第{lid}讲')}，打好基础",
                    "priority": "medium",
                })
                seen_ids.add(lid)

    # 去重、按优先级排序，最多 7 个
    recommendations.sort(key=lambda r: (0 if r["priority"] == "high" else 1, r["lecture_id"]))
    recommendations = recommendations[:7]

    # 生成总结
    weak_names = [d[0] for d in weak_dims[:2]]
    summary = f"根据你的画像，重点加强「{'」和「'.join(weak_names)}」方向，共推荐 {len(recommendations)} 个讲次。"

    return recommendations, summary


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_courses(request: RecommendRequest):
    """根据画像薄弱维度推荐课程讲次"""
    try:
        weak = request.weak_dimensions if request.weak_dimensions else []
        strong = request.strong_dimensions if request.strong_dimensions else []

        recs, summary = _build_recommendations(weak, strong)

        # 尝试用 LLM 增强推荐总结（失败则用默认总结）
        try:
            llm = get_llm_client()
            weak_desc = ", ".join(f"{n}({s}分)" for n, s in weak[:3]) if weak else "无"
            prompt = f"学生的薄弱维度：{weak_desc}。请用 2-3 句中文给出针对 Python 数据分析课程的个性化学习建议，语气鼓励。"
            llm_summary = await llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=200
            )
            if llm_summary and len(llm_summary) > 10:
                summary = llm_summary
        except Exception:
            pass  # LLM 不可用时用默认总结

        return RecommendResponse(
            recommendations=[RecommendedLecture(**r) for r in recs],
            summary=summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.get("/path")
async def get_learning_path(user_id: int = Depends(get_current_user_id)):
    """LLM 驱动的个性化学习路径。

    从数据库获取 6 维画像分数，调用 PathPlannerAgent.plan()，
    用 LLM 分析强弱项后生成个性化路径和提升建议。
    """
    from ..agents.path_planner import PathPlannerAgent

    profile = get_profile(user_id)

    # 检查是否为新用户（没有任何维度评分）
    raw_scores = [
        profile.theoretical_basis,
        profile.coding_ability,
        profile.practical_ops,
        profile.troubleshooting,
        profile.data_thinking,
        profile.self_learning,
    ]
    has_any_score = any(s and s > 0 for s in raw_scores)

    if not has_any_score:
        return {
            "generated_by": "none",
            "overall_assessment": "尚未完成学情画像评估，无法生成个性化路径",
            "paths": [],
            "weak_focus": [],
            "overall_score": 0,
            "suggestions": ["请先完成学情画像评估，AI 将根据你的能力雷达图生成专属学习路径"],
            "lectures": [],
        }

    scores = [s if s and s > 0 else 50 for s in raw_scores]

    agent = PathPlannerAgent()
    result = agent.plan(scores)

    # 转换为推荐讲次列表（前端兼容格式）
    lectures = []
    dim_names = agent.DIM_NAMES
    weak_indices = sorted(range(len(scores)), key=lambda i: scores[i])[:2]

    for item in result.get("path", []):
        for lid in item.get("lectures", []):
            lectures.append({
                "lecture_id": lid,
                "title": f"第{lid}讲 - {item.get('module', '')}",
                "reason": item.get("reason", "个性化推荐"),
                "priority": "high" if item.get("focus") == "strengthen" else "medium",
                "module": item.get("module"),
                "estimated_hours": item.get("estimated_hours", 1.5),
            })

    return {
        "generated_by": result.get("generated_by", "unknown"),
        "overall_assessment": result.get("overall_assessment", ""),
        "paths": result.get("paths", []),  # 3-5 条路径
        "weak_focus": result.get("weak_focus", []),
        "overall_score": result.get("overall_score", 0),
        "suggestions": [
            f"重点加强「{dim_names[wi]}」（当前 {scores[wi]} 分）"
            for wi in weak_indices
        ],
    }


async def get_dynamic_scores(user_id: int = Depends(get_current_user_id)) -> dict:
    """返回领域技能画像（已通过 Quiz/Lab 由 AssessmentAgent 实时更新，无需再计算六维加分）。"""
    profile = get_profile(user_id)
    return dict(profile.domain_skills or {})


@router.get("/dynamic/{user_id}")
async def get_dynamic_profile(user_id: int = Depends(get_current_user_id)):
    """返回领域技能画像 + 最近变化（随学随新）"""
    from ..core.database import get_connection
    from ..models.profile import get_domain_skill_changes

    profile = get_profile(user_id)
    domain_skills = profile.domain_skills or {}
    valid = [v for v in domain_skills.values() if v > 0]
    overall = round(sum(valid) / len(valid)) if valid else 0

    with get_connection() as db:
        qt = db.execute('SELECT COUNT(*) FROM quiz_attempts WHERE learner_id=?', (str(user_id),)).fetchone()[0]
        lc = db.execute("SELECT COUNT(*) FROM learning_events WHERE learner_id=? AND event_type='lab_completed'", (str(user_id),)).fetchone()[0]
        # completed_lectures is historically stored as daily increments; cap at the
        # actual 20-lecture Python data-analysis course to avoid impossible rates.
        lec = db.execute('SELECT COALESCE(SUM(completed_lectures), 0) FROM learning_records WHERE user_id=?', (user_id,)).fetchone()[0] or 0
        lec = min(int(lec), 20)
        tm = db.execute('SELECT SUM(study_minutes) FROM learning_records WHERE user_id=?', (user_id,)).fetchone()[0] or 0

    return {
        'profile': {'domain_skills': domain_skills, 'overall_score': overall},
        'changes': [],
        'domain_changes': get_domain_skill_changes(user_id),
        'quiz_attempts': qt,
        'labs_completed': lc,
        'lectures_completed': lec,
        'study_minutes': tm,
    }


@router.post("/heartbeat")
async def learning_heartbeat(user_id: int = Depends(get_current_user_id)):
    """前端每 60 秒调用一次，记录学习时长（学生端全局计时）"""
    from ..core.database import get_connection
    from datetime import date

    today = date.today().isoformat()
    with get_connection() as db:
        existing = db.execute(
            "SELECT id, study_minutes FROM learning_records WHERE user_id=? AND date=?",
            (user_id, today)
        ).fetchone()
        if existing:
            db.execute(
                "UPDATE learning_records SET study_minutes = study_minutes + 1 WHERE id=?",
                (existing["id"],)
            )
        else:
            db.execute(
                "INSERT INTO learning_records (user_id, date, completed_lectures, study_minutes) VALUES (?, ?, 0, 1)",
                (user_id, today)
            )
        db.commit()
        total = db.execute(
            "SELECT SUM(study_minutes) FROM learning_records WHERE user_id=?", (user_id,)
        ).fetchone()[0] or 0
    return {"study_minutes_today": existing["study_minutes"] + 1 if existing else 1, "study_minutes_total": total}


@router.get("/events")
async def profile_events(user_id: int = Depends(get_current_user_id)):
    """SSE 推送画像更新"""
    from fastapi.responses import StreamingResponse
    import asyncio
    import json as json_mod

    async def event_generator():
        last = None
        while True:
            p = get_profile(user_id)
            if p.updated_at != last:
                last = p.updated_at
                yield f"data: {json_mod.dumps({'type': 'profile_updated', 'data': {'theoretical_basis': p.theoretical_basis, 'coding_ability': p.coding_ability, 'practical_ops': p.practical_ops, 'troubleshooting': p.troubleshooting, 'data_thinking': p.data_thinking, 'self_learning': p.self_learning, 'overall_score': p.overall_score, 'completion_percentage': p.completion_percentage}})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
