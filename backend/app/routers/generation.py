"""Resource and quiz generation routes.

/api/generate/resource — 资源生成：创建任务 → DocAgent 生成讲义 → 持久化 → 返回结果。
/api/generate/quiz     — 题库生成（使用静态题库+LLM出题）。
/api/generate/tutor    — AI答疑（RAG驱动）。
"""
import asyncio
import re
import uuid
import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from ..agents.tutor_agent import TutorAgent, clean_tutor_visible_text
from ..schemas import ResourceRequest, TutorRequest, QuizGenerateRequest
from ..core.database import get_connection

router = APIRouter(prefix="/api/generate", tags=["generation"])


# ========== 资源生成任务持久化 ==========

def _ensure_resource_table(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS generated_resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE, user_id INTEGER, username TEXT,
        topic TEXT, content TEXT, code TEXT, citations_json TEXT,
        mindmap_json TEXT, quiz_json TEXT,
        status TEXT DEFAULT 'pending_review', review_status TEXT DEFAULT 'pending_review',
        reviewer_id INTEGER, review_reason TEXT, reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    # 为旧表添加缺失列（若不存在）
    for col, default in [("error_message", "''"), ("mindmap_json", "'[]'"), ("quiz_json", "'{}'")]:
        try:
            conn.execute(f"ALTER TABLE generated_resources ADD COLUMN {col} TEXT DEFAULT {default}")
        except Exception:
            pass  # 列已存在则忽略
    conn.commit()


def _create_task(task_id: str, topic: str, user_id: int = 0, username: str = "anonymous") -> int:
    """在 generated_resources 中创建 processing 状态的任务记录。"""
    with get_connection() as conn:
        _ensure_resource_table(conn)
        conn.execute("""INSERT OR REPLACE INTO generated_resources
            (task_id, user_id, username, topic, content, code, citations_json, status, review_status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (task_id, user_id, username, topic, "", "", "[]",
             "processing", "pending_review", datetime.now(timezone.utc).isoformat()))
        conn.commit()
        return conn.execute(
            "SELECT id FROM generated_resources WHERE task_id=?", (task_id,)
        ).fetchone()[0]


def _save_task_result(task_id: str, content: str, code: str, citations: list,
                      status: str = "pending_review", error_message: str = None,
                      mindmap: list = None, quiz: dict = None):
    """更新任务结果（成功或失败）。"""
    import json as json_mod
    with get_connection() as conn:
        _ensure_resource_table(conn)
        conn.execute("""UPDATE generated_resources SET
            content=?, code=?, citations_json=?, mindmap_json=?, quiz_json=?,
            status=?, error_message=?, review_status=?
            WHERE task_id=?""",
            (content, code, json_mod.dumps(citations, ensure_ascii=False),
             json_mod.dumps(mindmap or [], ensure_ascii=False),
             json_mod.dumps(quiz or {}, ensure_ascii=False),
             status, error_message, status, task_id))
        conn.commit()


def _get_task(task_id: str) -> dict | None:
    """查询任务记录。"""
    with get_connection() as conn:
        _ensure_resource_table(conn)
        row = conn.execute(
            "SELECT * FROM generated_resources WHERE task_id=?", (task_id,)
        ).fetchone()
        return dict(row) if row else None


# ========== 前端兼容的资源格式转换 ==========

def _to_frontend_format(topic: str, result: dict) -> dict:
    """将 orchestrator/DocAgent 返回结果转为前端 { topic, resources, sources } 格式。"""
    # 提取内容
    content = result.get("content", "")
    code = result.get("code", "")
    mindmap = result.get("mindmap", [])
    citations = result.get("citations", [])

    # 从 HTML 讲义中提取关键要点作为 summary（清洗 HTML 标签）
    import re as _re
    plain = _re.sub(r'<[^>]+>', '', content) if content else ""
    # 先尝试取 <li> 中的内容，否则按句号拆分
    bullets = _re.findall(r'<li>(.*?)</li>', content)
    if not bullets:
        sentences = [s.strip() for s in plain.replace('\n', ' ').split('。') if s.strip()]
        bullets = sentences[:5]
    summary_points = [_re.sub(r'<[^>]+>', '', b).strip()[:120] for b in bullets[:5] if b.strip()]

    resources = []
    if summary_points:
        resources.append({"type": "summary", "title": topic, "content": summary_points})
    if code:
        resources.append({"type": "code", "title": f"{topic} 代码示例", "content": code, "language": "python"})
    if mindmap:
        resources.append({"type": "mindmap", "title": f"{topic} 思维导图", "content": mindmap})

    sources = [
        {
            "asset_id": c.get("source", c.get("source_id", "")),
            "title": c.get("title", ""),
            "category": "knowledge_base",
            "source_path": c.get("source", c.get("source_path", "")),
            "score": 0.8,
        }
        for c in citations[:5]
    ]

    return {"topic": topic, "resources": resources, "sources": sources}


# ========== 路由 ==========

@router.post("/resource")
async def generate_resource(req: ResourceRequest):
    """
    资源生成 — 创建任务，进入 DocAgent 生成流程，持久化结果。

    流程:
      1. 校验输入（Pydantic 自动完成；JSON 格式错 → 400，字段缺 → 422）
      2. 创建 generated_resources 任务记录（status=processing）
      3. 调用 DocAgent + VerificationOrchestrator 管线生成讲义
      4. 成功 → 写入 DB（status=pending_review），返回前端兼容格式
      5. 失败 → 写入 DB（status=failed, error_message），返回安全错误
    """
    import json as json_mod

    topic = req.topic.strip()
    task_id = str(uuid.uuid4())[:12]

    # 1. 创建任务记录
    try:
        _create_task(task_id, topic, req.user_id, req.username)
        # 通过 event_bus 发送 SSE 事件（前端可通过 /api/events/stream 监听）
        from ..core.event_bus import event_bus
        await event_bus.publish("generation_agent_started", {
            "task_id": task_id, "topic": topic, "agent": "DocAgent",
            "message": f"开始生成讲义: {topic}",
        }, source="generate_resource")
    except Exception as e:
        print(f"[generate_resource] 创建任务失败: {e}")

    # 2. 生成内容（带超时保护）
    try:
        from app.agents.doc_agent import DocAgent

        # 先用 DocAgent 快速生成讲义（绕过完整审核管线，更快）
        # 防幻觉：先检索知识库证据，给快速路径也接地
        kb_sources = []
        try:
            from app.agents.knowledge_agent import KnowledgeRetrievalAgent
            kb_sources = KnowledgeRetrievalAgent().retrieve(topic, top_k=5)
        except Exception as kb_err:
            print(f"[generate_resource] 知识库检索失败: {kb_err}")

        agent = DocAgent()
        profile = dict(req.profile or {})
        profile.setdefault("user_id", req.user_id)
        profile.setdefault("username", req.username)
        profile.setdefault("path_type", req.path_type)
        state = {
            "lecture_topic": topic,
            "profile": profile,
            "mode": "study",
            "knowledge_context": {"sources": kb_sources, "topic": topic},
        }
        doc_result = await asyncio.wait_for(
            agent.execute(state),
            timeout=180.0,
        )
        content = doc_result.get("lecture_doc", {}).get("content", "")

        # 尝试完整审核管线（可选，有额外超时保护）
        code = ""
        mindmap = []
        quiz = {}
        citations = []
        gen_status = "pending_review"
        try:
            from app.agents.verification_orchestrator import get_verification_orchestrator
            orch = get_verification_orchestrator()
            orch_result = await asyncio.wait_for(
                orch.run(
                    course_id="python-data-analysis",
                    lecture_num=1,
                    course_title="Python数据分析实战",
                    lecture_topic=topic,
                    profile=profile,
                    mode="study",
                ),
                timeout=300.0,  # orchestrator 完整审核管线约需 2-5 分钟，给足上限让审核真正跑完
            )
            code = orch_result.get("code", "")
            mindmap = orch_result.get("mindmap", [])
            quiz = orch_result.get("quiz", {})
            citations = orch_result.get("citations", [])
            if orch_result.get("status") == "approved":
                gen_status = "approved"
            # 讲义与导图必须同步：只要 orchestrator 生成了有效内容，
            # 就统一采用它的 content + mindmap + code（同一次生成，天然一致），
            # 而不是拿首轮 DocAgent 的 content 去配 orchestrator 的 mindmap。
            orch_content = orch_result.get("content", "")
            if orch_content and len(orch_content) > 200:
                content = orch_content
        except (asyncio.TimeoutError, Exception) as orch_err:
            # orchestrator 超时/失败不影响 DocAgent 已生成的结果
            print(f"[generate_resource] orchestrator 超时/失败，使用 DocAgent 内容: {orch_err}")

        # 导图与讲义同步：始终从最终讲义内容确定性抽取 h3 章节 + strong 重点关键词，
        # 保证导图跟讲义严格对齐、且可学习（不走 LLM，避免拿到 "详见讲义内容"/"内容概述" 这类空泛结果）。
        if content:
            try:
                from app.agents.mindmap_agent import MindmapAgent
                mm_agent = MindmapAgent()
                mm_parsed = mm_agent._extract_from_html(content, topic)
                if not mm_parsed:
                    mm_parsed = mm_agent._fallback(topic)
                mindmap = (mm_parsed or {}).get("nodes", [])
                if mindmap:
                    print(f"[generate_resource] 从讲义生成导图完成，{len(mindmap)} 个根节点")
            except Exception as e:
                print(f"[generate_resource] 从讲义生成导图失败: {e}")

        # 3. 保存成功结果
        if content and len(content) > 200:
            _save_task_result(task_id, content, code, citations, status=gen_status,
                              mindmap=mindmap, quiz=quiz)
            result = _to_frontend_format(
                topic,
                {"content": content, "code": code, "mindmap": mindmap,
                 "quiz": quiz, "citations": citations}
            )
            result["task_id"] = task_id
            result["status"] = gen_status
            await event_bus.publish("resource_generated", {
                "task_id": task_id, "topic": topic,
                "content_length": len(content), "status": gen_status,
            }, source="generate_resource")
            await event_bus.publish("generation_completed", {
                "task_id": task_id, "topic": topic, "status": gen_status,
                "message": f"讲义生成完成: {len(content)} 字符",
            }, source="generate_resource")
            return result  # FastAPI 自动序列化为 JSON
        else:
            raise RuntimeError(f"DocAgent 生成内容过短 ({len(content)} chars)")

    except asyncio.TimeoutError:
        _save_task_result(task_id, "", "", [], status="failed",
                          error_message="请求超时：讲义生成超过 180 秒限制，请稍后重试")
        await event_bus.publish("generation_failed", {
            "task_id": task_id, "topic": topic,
            "error": "timeout", "message": "请求超时（>180s）",
        }, source="generate_resource")
        raise HTTPException(status_code=504, detail="讲义生成超时（>180s），请稍后重试")

    except HTTPException:
        raise  # 不要拦截已有的 HTTPException

    except Exception as e:
        error_msg = str(e)[:500]
        if "402" in error_msg or "Insufficient" in error_msg or "insufficient" in error_msg:
            _save_task_result(task_id, "", "", [], status="failed", error_message="LLM 账户额度不足（HTTP 402）")
            await event_bus.publish("generation_failed", {"task_id": task_id, "topic": topic, "error": "LLM quota insufficient"}, source="generate_resource")
            raise HTTPException(status_code=402, detail="大模型账户额度不足（HTTP 402），请充值或更换可用的 API Key 后重试")
        safe_msg = "讲义生成失败，请检查后端服务状态或稍后重试"
        traceback.print_exc()
        _save_task_result(task_id, "", "", [], status="failed", error_message=error_msg)
        await event_bus.publish("generation_failed", {
            "task_id": task_id, "topic": topic,
            "error": error_msg[:200],
        }, source="generate_resource")
        raise HTTPException(status_code=500, detail=safe_msg)


@router.get("/resource/{task_id}")
def get_resource_task(task_id: str):
    """查询资源生成任务状态和结果。GET /api/generate/resource/:task_id"""
    task = _get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

    import json as json_mod
    citations = []
    try:
        citations = json_mod.loads(task.get("citations_json", "[]"))
    except Exception:
        pass

    mindmap = []
    try:
        mindmap = json_mod.loads(task.get("mindmap_json", "[]"))
    except Exception:
        pass

    quiz = {}
    try:
        quiz = json_mod.loads(task.get("quiz_json", "{}"))
    except Exception:
        pass

    return {
        "task_id": task["task_id"],
        "topic": task["topic"],
        "status": task["status"],
        "content": task.get("content", ""),
        "code": task.get("code", ""),
        "mindmap": mindmap,
        "quiz": quiz,
        "citations": citations,
        "error_message": task.get("error_message", ""),
        "created_at": task.get("created_at", ""),
    }


# ========== Quiz & Tutor（保留兼容） ==========

def _strip_markdown(text: str) -> str:
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-*]{3,}\s*$', '', text, flags=re.MULTILINE)
    lines = text.split('\n')
    clean_lines = []
    skip = False
    for line in lines:
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            if re.match(r'^\|[\s\-:|]+\|$', s):
                skip = True; continue
            if skip or '|' in s[1:-1]:
                cells = [c.strip() for c in s[1:-1].split('|')]
                clean_lines.append('：'.join(cells))
                skip = True; continue
        skip = False
        line = re.sub(r'^(\s*)[-*]\s+', r'\1· ', line)
        line = re.sub(r'`([^`]+)`', r'\1', line)
        clean_lines.append(line)
    text = '\n'.join(clean_lines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _build_learner_profile(p) -> dict:
    """从 LearnerProfile 提取 LLM 出题所需的画像摘要字段。"""
    from ..models.profile import DOMAIN_SKILL_LABELS
    return {
        "user_id": p.user_id,
        "major_background": p.major_background,
        "six_dims": {
            "理论基础": p.theoretical_basis,
            "编程能力": p.coding_ability,
            "实践操作": p.practical_ops,
            "问题排查": p.troubleshooting,
            "数据思维": p.data_thinking,
            "自学能力": p.self_learning,
        },
        "domain_skills": {DOMAIN_SKILL_LABELS.get(k, k): v for k, v in (p.domain_skills or {}).items()},
        "weak_dimensions": p.weak_dimensions,
        "strong_dimensions": p.strong_dimensions,
        "domain_weak_skills": p.domain_weak_skills,
        "domain_strong_skills": p.domain_strong_skills,
        "cognitive_style": p.cognitive_style,
        "learning_pace": p.learning_pace,
        "learning_motivation": p.learning_motivation,
    }


@router.post("/quiz")
async def generate_quiz(req: QuizGenerateRequest):
    topic = req.topic or "Python 基础"
    subtopic = req.subtopic or topic
    count = req.count or 5
    lecture = getattr(req, "lecture", None)

    # 纯个性化出题：读完整画像 → 交给 QuizAgent，基于画像 + RAG 证据生成专属题组。
    from ..agents.quiz_agent import get_quiz_agent
    from ..models.profile import get_profile

    try:
        p = get_profile(req.user_id) if req.user_id else None
        learner_profile = _build_learner_profile(p) if p else None
        domain = (p.domain_skills or {}) if p else {}
        score = round(sum(domain.values()) / max(1, len(domain))) if domain else 0
        result = get_quiz_agent().generate(
            topic=topic,
            count=count,
            difficulty=req.difficulty,
            profile=req.profile,
            domain_context={'score': score, 'path_type': 'quiz_page', 'lecture': lecture or '', 'subtopic': subtopic},
            learner_profile=learner_profile,
        )
        if result.get('questions'):
            return result
    except Exception as e:
        print(f"[generate_quiz] 个性化出题异常: {e}")

    # 个性化出题失败：返回空题组 + 明确提示，不再回退静态题库。
    return {"topic": topic, "questions": [], "sources": [], "generated_by": "llm", "empty": True, "error": "个性化出题失败，请稍后重试"}


@router.post("/tutor")
async def generate_tutor_answer(req: TutorRequest):
    result = await TutorAgent().answer_with_history(req.question, req.history, req.topic)
    if isinstance(result, dict) and 'answer' in result:
        result['answer'] = clean_tutor_visible_text(_strip_markdown(result['answer']))
    return result
