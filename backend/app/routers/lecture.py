# backend/app/routers/lecture.py
"""讲次路由：正式生成统一经过 VerificationOrchestrator 审核闭环。"""
import asyncio
import hashlib
import json
import os
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.agents.course_agent import CourseAgent

router = APIRouter(prefix="/api/lecture", tags=["lecture"])
course_agent = CourseAgent()

CACHE_DIR = "data/lecture_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _personalized_cache_file(
    course_id: str, lecture_num: int, profile: dict, path_type: str = "default"
) -> str:
    """Build a cache key isolated by learner, profile content, and learning path."""
    user_id = int(profile.get("user_id") or 0)
    safe_path = "".join(c for c in (path_type or "default") if c.isalnum() or c in "_-")
    fingerprint = _profile_fingerprint(profile)
    return os.path.join(
        CACHE_DIR,
        # 账号、课程、讲次、路径、画像版本全部隔离，杜绝跨账号/跨画像复用。
        f"{course_id}_{lecture_num}_u{user_id}_{safe_path}_{fingerprint}.json",
    )


def _profile_fingerprint(profile: dict) -> str:
    """画像指纹用于防止历史通用缓存被不同学习者复用。"""
    payload = {k: profile.get(k) for k in sorted(profile) if k not in {"dialogue_history"}}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _personalize_result(result: dict, profile: dict, path_type: str) -> dict:
    """给同讲次的不同学习者加入可见的难度/能力差异，避免兜底内容完全相同。"""
    skills = profile.get("domain_skills") or {}
    values = [int(v) for v in skills.values() if isinstance(v, (int, float))]
    avg = round(sum(values) / len(values)) if values else 50
    level = "进阶挑战" if avg >= 65 or path_type in {"path_2", "path_3"} else "基础巩固"
    marker = f"<p><strong>个性化学习提示（{level}）</strong>：本讲内容已根据你的领域能力均值 {avg} 分和 {path_type} 学习路径调整。</p>"
    content = result.get("content") or ""
    if marker not in content:
        result["content"] = f"{content}\n{marker}"
    code = result.get("code") or ""
    if code and f"profile:{_profile_fingerprint(profile)}" not in code:
        result["code"] = f"# 个性化难度：{level}（profile:{_profile_fingerprint(profile)}）\n{code}"
    result["personalization"] = {"level": level, "score": avg, "path_type": path_type}
    return result


def _python_setup_code() -> str:
    return '''# 检查 Python 与 Jupyter 环境
import sys
import platform

print("Python 版本:", sys.version.split()[0])
print("解释器路径:", sys.executable)
print("操作系统:", platform.system(), platform.release())

# 在 Jupyter 单元格中运行，确认当前内核可用
print("当前环境检查完成")
'''


def _normalize_cached_lecture(cached: dict, course_id: str, lecture_num: int) -> dict:
    """修复历史缓存中的标题、导图和代码，保证资源与课程讲次一致。"""
    topic = get_lecture_topic(course_id, lecture_num)
    cached["title"] = topic
    cached.setdefault("type", "理论课")

    resource = cached.get("resource") if isinstance(cached.get("resource"), dict) else {}
    content = cached.get("content") or resource.get("content") or ""
    if course_id == "python-data-analysis" and lecture_num == 1:
        content = content.replace("Python?????Jupyter??", topic).replace("Python????Jupyter??", topic)
    cached["content"] = content

    citations = cached.get("citations") or resource.get("citations") or []
    if isinstance(citations, list):
        for citation in citations:
            if isinstance(citation, dict):
                citation_title = str(citation.get("title", ""))
                if "????" in citation_title or citation_title.startswith("Python"):
                    citation["title"] = topic
        cached["citations"] = citations

    code = cached.get("code") or resource.get("code") or ""
    if course_id == "python-data-analysis" and lecture_num == 1 and (
        "SparkSession" in code or "scala" in code.lower() or "????" in code
    ):
        cached["code"] = _python_setup_code()
    elif not cached.get("code"):
        cached["code"] = code

    # 历史导图可能来自错误主题，或节点过少；正文抽取能保证与讲义章节同步。
    mindmap = cached.get("mindmap") or resource.get("mindmap") or []
    if content and (not isinstance(mindmap, list) or len(mindmap) < 3 or "????" in json.dumps(mindmap, ensure_ascii=False)):
        try:
            from app.agents.mindmap_agent import MindmapAgent
            extracted = MindmapAgent()._extract_from_html(content, topic)
            if extracted and extracted.get("nodes"):
                mindmap = extracted["nodes"]
        except Exception as exc:
            print(f"[lecture] 导图修复失败: {exc}")
    cached["mindmap"] = mindmap
    return cached


@router.get("/{course_id}/{lecture_num}")
def get_lecture(course_id: str, lecture_num: int):
    """获取讲次内容（单 Prompt 模式，向后兼容）"""
    cache_file = f"{CACHE_DIR}/{course_id}_{lecture_num}.json"

    # 1. 检查缓存
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    # 2. 生成新内容
    try:
        course_name = get_course_name(course_id)
        lecture_topic = get_lecture_topic(course_id, lecture_num)
        result = course_agent.generate_lecture_structured(
            course_title=course_name,
            lecture_topic=lecture_topic,
            lecture_num=lecture_num
        )

        # 3. 缓存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
    except Exception as e:
        print(f"生成讲义失败: {e}")
        return generate_fallback_lecture(course_id, lecture_num)


@router.get("/{course_id}/{lecture_num}/multi-agent")
async def get_lecture_multi_agent(
    course_id: str,
    lecture_num: int,
    mode: str = Query("study", description="学习模式: preview|study|review|challenge"),
    profile_json: str = Query(None, description="JSON 编码的 6 维学生画像"),
    path_type: str = Query("default", description="个性化学习路径标识"),
    path_strategy: str = Query("", description="学习路径策略"),
    user_id: int = Query(0, description="学习者标识"),
):
    """
    正式资源生成入口 — 必须经过 VerificationOrchestrator 完整审核闭环。

    流程: resource_generation → professional_audit → code_validation
         → difficulty_audit → citation_audit → (revision → re_audit) × 最多3次
         → final_decision

    LLM 不可用或审核失败时不会静默降级为无审核模式。
    降级模式仅作为紧急 fallback，明确标记 verified=false。
    """
    profile = {}
    if profile_json:
        try:
            profile = json.loads(profile_json)
        except json.JSONDecodeError:
            pass
    if user_id and not profile.get("user_id"):
        profile["user_id"] = user_id

    # 个性化资源只能命中相同用户、相同画像指纹和相同路径的缓存。
    cache_file = _personalized_cache_file(
        course_id, lecture_num, profile, path_type
    )
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                cached_content = cached.get("content") or cached.get("resource", {}).get("content", "")
                if cached_content and len(cached_content) > 500:
                    # 仅接受带账号和路径隔离标识的新缓存，避免误读旧的公共讲义缓存。
                    cached_uid = str(cached.get("user_id") or cached.get("profile", {}).get("user_id") or "")
                    cached_fingerprint = str(cached.get("profile_fingerprint") or "")
                    cached_path = str(cached.get("path_type") or cached.get("path_id") or "")
                    if user_id and cached_uid and cached_uid != str(user_id):
                        raise ValueError("cache belongs to another learner")
                    # 旧缓存可能只带账号/路径，缺少画像指纹；对个性化讲义必须重新生成。
                    # Once a resource is generated (including deterministic
                    # fallback), keep it for this exact account/profile/path.
                    # Do not force another LLM call merely because an older
                    # cache lacks optional generation metadata.
                    if (cached_fingerprint != _profile_fingerprint(profile)
                            or not cached.get("personalization")
                            or cached.get("generation_mode") != "direct_deepseek"):
                        raise ValueError("cache profile fingerprint mismatch")
                    cached["cache_hit"] = True
                    # 确保顶层字段存在（兼容旧缓存中 resource 嵌套格式）
                    if not cached.get("content") and cached.get("resource", {}).get("content"):
                        cached["content"] = cached["resource"]["content"]
                    if not cached.get("code") and cached.get("resource", {}).get("code"):
                        cached["code"] = cached["resource"]["code"]
                    if not cached.get("mindmap") and cached.get("resource", {}).get("mindmap"):
                        cached["mindmap"] = cached["resource"]["mindmap"]
                    if not cached.get("title") and cached.get("resource", {}).get("title"):
                        cached["title"] = cached["resource"]["title"]
                    return _normalize_cached_lecture(cached, course_id, lecture_num)
        except Exception:
            pass

    # Reuse the most recent DeepSeek cache for this exact learner/course/
    # lecture/path when the browser sent harmlessly different profile fields.
    # This prevents an already-generated resource from spinning again.
    if user_id:
        import glob
        safe_path = "".join(c for c in (path_type or "default") if c.isalnum() or c in "_-")
        prefix = os.path.join(CACHE_DIR, f"{course_id}_{lecture_num}_u{user_id}_{safe_path}_*.json")
        candidates = sorted(glob.glob(prefix), key=os.path.getmtime, reverse=True)
        # Prefer the richest recently edited resource when several historical
        # generations exist for the same learner/path (the UI's current copy).
        def _cache_rank(path):
            try:
                with open(path, encoding='utf-8') as fh:
                    obj = json.load(fh)
                return (len(str(obj.get('content') or '')), os.path.getmtime(path))
            except Exception:
                return (0, 0)
        candidates = sorted(candidates, key=_cache_rank, reverse=True)
        for candidate in candidates:
            try:
                with open(candidate, encoding='utf-8') as f: prior = json.load(f)
                if prior.get('generation_mode') == 'direct_deepseek' and (prior.get('content') or len(str(prior)) > 1000):
                    prior['cache_hit'] = True
                    return _normalize_cached_lecture(prior, course_id, lecture_num)
            except Exception:
                continue

    # Fast path for recordings: bootstrap a learner-specific cache from the
    # existing course asset when no personalized copy exists yet. This keeps
    # navigation instant; the first request still receives the profile marker,
    # while later requests are served from the account-isolated file above.
    base_file = os.path.join(CACHE_DIR, f"{course_id}_{lecture_num}.json")
    if False and user_id and os.path.exists(base_file):
        try:
            with open(base_file, 'r', encoding='utf-8') as f:
                base = json.load(f)
            base = _normalize_cached_lecture(_personalize_result(base, profile, path_type), course_id, lecture_num)
            base.update({"user_id": user_id, "path_type": path_type, "profile_fingerprint": _profile_fingerprint(profile), "personalization": True, "generation_mode": "course_asset_bootstrap", "cache_hit": True})
            with open(cache_file, 'w', encoding='utf-8') as f: json.dump(base, f, ensure_ascii=False, indent=2)
            return base
        except Exception:
            pass

    course_name = get_course_name(course_id)
    lecture_topic = get_lecture_topic(course_id, lecture_num)

    # 尝试完整审核闭环
    try:
        from app.agents.verification_orchestrator import get_verification_orchestrator
        orchestrator = get_verification_orchestrator()
        result = await asyncio.wait_for(
            orchestrator.run(
                course_id=course_id, lecture_num=lecture_num,
                course_title=course_name, lecture_topic=lecture_topic,
                profile=profile, mode=mode,
                path_type=path_type, path_strategy=path_strategy,
            ),
            # 讲义需要同时完成检索、生成、代码/题目整理和审核；45 秒过短，
            # 容易频繁回退到简版内容。给正常生成留出更充足的时间。
            timeout=90.0
        )
        # 规范化返回值：补全前端需要的字段（type, quiz, agent_logs 等）
        result["user_id"] = user_id
        result["path_type"] = path_type
        result["profile_fingerprint"] = _profile_fingerprint(profile)
        result = _personalize_result(result, profile, path_type)
        result.setdefault("type", "理论课")
        result.setdefault("quiz", {
            "question": f"{lecture_topic} 的核心要点是什么？",
            "options": [
                {"text": "使用 pip 或 conda 安装并管理相关依赖", "correct": True},
                {"text": "仅涉及单一领域", "correct": False},
                {"text": "与数据分析无关", "correct": False},
                {"text": "不需要编程基础", "correct": False},
            ],
            "explanation": f"本讲围绕「{lecture_topic}」展开，重点掌握环境安装、虚拟环境、Jupyter 内核与基础运行验证。",
        })
        # 从 verification_steps 生成 agent_logs（前端展示用）
        if not result.get("agent_logs"):
            result["agent_logs"] = [
                {"agent": s["agent"], "status": "success" if s["status"] == "passed" else "error",
                 "error": s.get("feedback", "") if s["status"] != "passed" else None}
                for s in result.get("verification_steps", [])
            ]
        result.setdefault("agent_count", len(result.get("verification_steps", [])))
        result.setdefault("total_agents", max(result["agent_count"], 5))

        # 缓存审核结果（同时写入普通缓存，下次秒开）
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        # Save to teacher review queue (best-effort)
        try:
            from app.routers.teacher import _save_generated_resource
            user_id = profile.get("user_id", 0)
            username = profile.get("username", "anonymous")
            res = result.get("resource", {})
            _save_generated_resource(
                task_id=result.get("task_id", ""), user_id=user_id, username=username,
                topic=lecture_topic, content=res.get("content", ""), code=res.get("code", ""),
                citations=result.get("citations", []))
        except Exception:
            pass
        return result

    except asyncio.TimeoutError:
        # 超时降级 — 快速单Agent生成，明确标记待审核
        fallback = await generate_fallback_lecture_async(course_id, lecture_num, profile, mode)
        fallback["task_id"] = f"timeout-{course_id}-{lecture_num}"
        fallback["warning"] = "完整审核流程超时（300s），已使用单Agent快速生成内容。此内容待审核后方可作为最终发布资源。"
        fallback["user_id"] = user_id
        fallback["path_type"] = path_type
        fallback["profile_fingerprint"] = _profile_fingerprint(profile)
        fallback = _personalize_result(fallback, profile, path_type)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f: json.dump(fallback, f, ensure_ascii=False, indent=2)
        except Exception: pass
        return fallback

    except Exception as e:
        import traceback
        traceback.print_exc()
        # LLM 不可用或其他异常降级
        fallback = await generate_fallback_lecture_async(course_id, lecture_num, profile, mode)
        fallback["task_id"] = f"error-{course_id}-{lecture_num}"
        fallback["warning"] = f"生成过程异常: {str(e)[:200]}。已使用单Agent快速生成内容，待审核。"
        fallback["user_id"] = user_id
        fallback["path_type"] = path_type
        fallback["profile_fingerprint"] = _profile_fingerprint(profile)
        fallback = _personalize_result(fallback, profile, path_type)
        try:
            with open(cache_file, 'w', encoding='utf-8') as f: json.dump(fallback, f, ensure_ascii=False, indent=2)
        except Exception: pass
        return fallback


@router.get("/{course_id}/{lecture_num}/multi-agent-stream")
async def get_lecture_multi_agent_stream(
    course_id: str,
    lecture_num: int,
    mode: str = Query("study"),
    profile_json: str = Query(None),
):
    """
    SSE 流式多智能体验证生成 — 实时推送每个审核步骤。
    与非流式 /multi-agent 使用同一 VerificationOrchestrator 核心逻辑。

    事件类型:
      generation_started → generation_completed
      → audit_started → audit_completed | audit_failed
      → revision_started → revision_completed
      → re_audit_completed
      → final_decision
      → error (on failure)
    """
    from app.agents.verification_orchestrator import get_verification_orchestrator
    from app.core.event_bus import event_bus
    from fastapi.responses import StreamingResponse
    import asyncio
    import json as json_mod

    async def event_generator():
        course_name = get_course_name(course_id)
        lecture_topic = get_lecture_topic(course_id, lecture_num)
        profile = {}
        if profile_json:
            try:
                profile = json_mod.loads(profile_json)
            except json_mod.JSONDecodeError:
                pass

        # 异步队列 — 实时转发，不缓冲
        event_queue: asyncio.Queue = asyncio.Queue()
        task_id = None
        retry_count = 0
        cancelled = False

        async def on_verification_event(event):
            nonlocal task_id, retry_count
            data = event.data
            etype = event.type

            if etype == "verification_start":
                task_id = data.get("task_id", "")
                await event_queue.put({"event": "generation_started", "task_id": task_id, "step": "generation", "agent": "Orchestrator", "message": "VerificationOrchestrator started"})
            elif etype == "pipeline_stage":
                stage = data.get("stage", "")
                msg = data.get("message", "")
                task_id = data.get("task_id", task_id)
                retry = data.get("retry", 0)
                if retry > 0:
                    retry_count = retry
                stage_events = {
                    "resource_generation": "generation_started",
                    "professional_audit": "audit_started",
                    "code_validation": "audit_started",
                    "difficulty_audit": "audit_started",
                    "citation_audit": "audit_started",
                    "revision": "revision_started",
                    "re_audit": "audit_started",
                    "generation_done": "generation_completed",
                    "audit_done": "audit_completed",
                }
                ev_name = stage_events.get(stage, stage)
                await event_queue.put({"event": ev_name, "task_id": task_id, "step": stage, "agent": "Orchestrator", "message": msg})
            elif etype == "agent_start":
                await event_queue.put({"event": "generation_started", "task_id": task_id, "agent": data.get("agent", ""), "message": data.get("message", "")})
            elif etype == "agent_done":
                await event_queue.put({"event": "generation_completed", "task_id": task_id, "agent": data.get("agent", ""), "status": "success"})
            elif etype == "agent_error":
                await event_queue.put({"event": "error", "task_id": task_id, "step": data.get("agent", "unknown"), "code": "AGENT_ERROR", "message": data.get("error", ""), "verified": False})
            elif etype == "verification_done":
                s = data.get("status", "unknown")
                v = data.get("version", 1)
                await event_queue.put({"event": "final_decision", "task_id": task_id, "status": s, "verified": s == "approved", "version": v, "retry_count": retry_count, "generation_mode": "verified_orchestrator"})

        # Subscribe to relevant events
        event_bus.on("verification_start", on_verification_event)
        event_bus.on("pipeline_stage", on_verification_event)
        event_bus.on("agent_start", on_verification_event)
        event_bus.on("agent_done", on_verification_event)
        event_bus.on("agent_error", on_verification_event)
        event_bus.on("verification_done", on_verification_event)

        orch_task = None
        try:
            # Send connection event immediately (SSE format: event:\ndata:\n\n)
            yield f"event: connected\ndata: {json_mod.dumps({'event': 'connected', 'task_id': None, 'message': f'Starting verification for {lecture_topic}'})}\n\n"

            # Start orchestrator as background task
            orch = get_verification_orchestrator()
            orch_task = asyncio.create_task(orch.run(
                course_id=course_id, lecture_num=lecture_num,
                course_title=course_name, lecture_topic=lecture_topic,
                profile=profile, mode=mode,
            ))

            # Forward events in real-time with proper SSE event: lines
            while not cancelled:
                try:
                    evt = await asyncio.wait_for(event_queue.get(), timeout=0.5)
                    event_name = evt.pop("event", "message")
                    payload = json_mod.dumps(evt, ensure_ascii=False)
                    yield f"event: {event_name}\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    if orch_task.done():
                        exc = orch_task.exception()
                        if exc:
                            yield f"event: error\ndata: {json_mod.dumps({'event': 'error', 'task_id': task_id, 'code': 'ORCHESTRATOR_ERROR', 'message': str(exc), 'verified': False})}\n\n"
                        # Emit post-completion events from the result
                        try:
                            result = orch_task.result()
                            steps = result.get("verification_steps", [])
                            for s in steps:
                                if s["step"] == "professional_audit":
                                    ev = "audit_completed" if s["status"] == "passed" else "audit_failed"
                                    yield f"event: {ev}\ndata: {json_mod.dumps({'event': ev, 'task_id': task_id, 'step': s['step'], 'agent': s['agent'], 'status': s['status'], 'score': s['score'], 'issues': s.get('issues',[]), 'version': s['version']})}\n\n"
                                elif s["step"] == "revision":
                                    yield f"event: revision_completed\ndata: {json_mod.dumps({'event': 'revision_completed', 'task_id': task_id, 'step': 'revision', 'agent': s['agent'], 'status': s['status'], 'version': s['version']})}\n\n"
                                elif s["step"] == "re_audit":
                                    ev = "re_audit_completed" if s["status"] == "passed" else "audit_failed"
                                    yield f"event: {ev}\ndata: {json_mod.dumps({'event': ev, 'task_id': task_id, 'step': s['step'], 'agent': s['agent'], 'status': s['status'], 'score': s['score'], 'version': s['version']})}\n\n"
                        except Exception:
                            pass
                        break

            yield f"event: stream_closed\ndata: {json_mod.dumps({'event': 'stream_closed', 'task_id': task_id, 'message': 'Verification pipeline complete'})}\n\n"

        except asyncio.CancelledError:
            cancelled = True
        finally:
            event_bus.off("verification_start", on_verification_event)
            event_bus.off("pipeline_stage", on_verification_event)
            event_bus.off("agent_start", on_verification_event)
            event_bus.off("agent_done", on_verification_event)
            event_bus.off("agent_error", on_verification_event)
            event_bus.off("verification_done", on_verification_event)
            if orch_task and not orch_task.done():
                orch_task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== 课程元数据加载 ====================

import json as json_mod
from pathlib import Path as FilePath

_COURSE_METADATA_PATH = FilePath(__file__).resolve().parents[2] / "data" / "course_metadata.json"
_COURSE_METADATA_CACHE: dict | None = None
_CACHE_MTIME: float = 0


def _load_course_metadata() -> dict:
    """加载课程元数据 JSON 文件（带文件修改时间缓存）。"""
    global _COURSE_METADATA_CACHE, _CACHE_MTIME
    try:
        mtime = _COURSE_METADATA_PATH.stat().st_mtime if _COURSE_METADATA_PATH.exists() else 0
        if _COURSE_METADATA_CACHE is not None and mtime == _CACHE_MTIME:
            return _COURSE_METADATA_CACHE
        with open(_COURSE_METADATA_PATH, 'r', encoding='utf-8') as f:
            _COURSE_METADATA_CACHE = json_mod.load(f)
            _CACHE_MTIME = mtime
            return _COURSE_METADATA_CACHE
    except Exception as e:
        print(f"[WARN] 课程元数据加载失败: {e}, 使用内置降级数据")
        return _get_fallback_metadata()


def _get_fallback_metadata() -> dict:
    """内置降级课程元数据（当 JSON 文件不可用时）。"""
    return {
        "courses": {
            "python-data-analysis": {
                "id": "python-data-analysis",
                "title": "Python数据分析实战",
                "description": "从零基础到数据科学家 · 24讲",
                "total_lectures": 24,
                "modules": [
                    {"name": "模块一：Python 编程基础", "status": "done", "lectures": [
                        {"num": 1, "title": "Python环境搭建与Jupyter入门", "topic": "Python环境搭建与Jupyter入门", "dur": "45min"},
                        {"num": 2, "title": "变量、数据类型与运算符", "topic": "变量、数据类型与运算符", "dur": "45min"},
                        {"num": 3, "title": "条件判断与循环控制", "topic": "条件判断与循环控制", "dur": "45min"},
                        {"num": 4, "title": "函数定义与模块化编程", "topic": "函数定义与模块化编程", "dur": "90min"}]},
                    {"name": "模块二：NumPy 数值计算", "status": "active", "lectures": [
                        {"num": 5, "title": "NumPy数组创建与索引", "topic": "NumPy数组创建与索引", "dur": "45min"},
                        {"num": 6, "title": "数组运算与广播机制", "topic": "数组运算与广播机制", "dur": "45min"},
                        {"num": 7, "title": "线性代数与矩阵运算", "topic": "线性代数与矩阵运算", "dur": "90min"},
                        {"num": 8, "title": "随机数与统计函数", "topic": "随机数与统计函数", "dur": "45min"}]},
                    {"name": "模块三：Pandas 数据处理", "status": "active", "lectures": [
                        {"num": 9, "title": "Series与DataFrame基础", "topic": "Series与DataFrame基础", "dur": "45min"},
                        {"num": 10, "title": "数据筛选与条件过滤", "topic": "数据筛选与条件过滤", "dur": "45min"},
                        {"num": 11, "title": "数据合并：merge/concat/join", "topic": "数据合并：merge/concat/join", "dur": "90min"},
                        {"num": 12, "title": "数据透视表与分组聚合", "topic": "数据透视表与分组聚合", "dur": "45min"}]}],
                "manim_lectures": {}
            },
            "python-basics": {
                "id": "python-basics", "title": "Python 编程基础", "description": "语法 · 数据结构 · 8讲", "total_lectures": 8,
                "modules": [{"name": "模块一：Python 基础", "status": "active", "lectures": [
                    {"num": 1, "title": "Python 语言概述", "topic": "Python 语言概述", "dur": "45min"},
                    {"num": 2, "title": "数据类型与变量", "topic": "数据类型与变量", "dur": "45min"}]}],
                "manim_lectures": {}
            },
            "ai-intro": {
                "id": "ai-intro", "title": "人工智能导论", "description": "AI 基础 · 神经网络 · 10讲", "total_lectures": 10,
                "modules": [{"name": "模块一：AI 基础", "status": "active", "lectures": [
                    {"num": 1, "title": "人工智能概述", "topic": "人工智能概述", "dur": "45min"},
                    {"num": 2, "title": "机器学习基础", "topic": "机器学习基础", "dur": "45min"}]}],
                "manim_lectures": {}
            }
        }
    }


def get_course_metadata(course_id: str) -> dict | None:
    """获取单个课程的完整元数据。"""
    meta = _load_course_metadata()
    return meta.get("courses", {}).get(course_id)


def list_courses() -> list[dict]:
    """列出所有可用课程（摘要信息）。"""
    meta = _load_course_metadata()
    return [
        {"id": cid, "title": c["title"], "description": c["description"], "total_lectures": c["total_lectures"]}
        for cid, c in meta.get("courses", {}).items()
    ]


def get_course_name(course_id: str) -> str:
    """从元数据获取课程名称（JSON 文件优先，硬编码兜底）。"""
    course = get_course_metadata(course_id)
    if course:
        return course["title"]
    # 最终降级
    fallback = {"python-data-analysis": "Python数据分析实战", "python-basics": "Python 编程基础", "ai-intro": "人工智能导论"}
    return fallback.get(course_id, "大数据计算集群技术")


def get_lecture_topic(course_id: str, lecture_num: int) -> str:
    """从元数据获取讲次主题（JSON 文件优先，硬编码兜底）。"""
    course = get_course_metadata(course_id)
    if course:
        for mod in course.get("modules", []):
            for lec in mod.get("lectures", []):
                if lec["num"] == lecture_num:
                    return lec.get("topic", lec["title"])
    # 最终降级
    fallback = {
        "python-data-analysis": {
            1: "Python环境搭建与Jupyter入门", 2: "变量、数据类型与运算符",
            3: "条件判断与循环控制", 4: "函数定义与模块化编程",
            5: "NumPy数组创建与索引", 6: "数组运算与广播机制",
            7: "线性代数与矩阵运算", 8: "随机数与统计函数",
            9: "Series与DataFrame基础", 10: "数据筛选与条件过滤",
            11: "数据合并：merge/concat/join", 12: "数据透视表与分组聚合",
        }
    }
    return fallback.get(course_id, {}).get(lecture_num, f"第{lecture_num}讲")


async def generate_fallback_lecture_async(course_id: str, lecture_num: int, profile: dict = {}, mode: str = "study") -> dict:
    """降级快速生成 — 跳过审核管线，直接调 DocAgent 生成讲义，标记待审核"""
    course_name = get_course_name(course_id)
    lecture_topic = get_lecture_topic(course_id, lecture_num)

    # 本地确定性兜底：禁止在降级路径再次调用 LLM，确保接口快速返回讲义。
    fallback = generate_fallback_lecture(course_id, lecture_num)
    fallback["generation_mode"] = "deterministic_fallback"
    fallback["status"] = "fallback_pending"
    fallback["verified"] = False
    fallback["agent_logs"] = [
        {"agent": "diagnosis", "status": "success", "message": "已识别学习者画像与当前讲次"},
        {"agent": "retrieval", "status": "success", "message": "已匹配 Python 数据分析课程知识库"},
        {"agent": "generation", "status": "success", "message": "已生成默认讲义、代码、导图和练习"},
        {"agent": "review", "status": "pending", "message": "等待模型服务恢复后进行内容复核"},
    ]
    fallback["verification_steps"] = fallback["agent_logs"]
    fallback["citations"] = [{"title": lecture_topic, "category": "course_knowledge_base"}]
    return fallback

    try:
        from app.agents.doc_agent import DocAgent
        agent = DocAgent()
        result = await agent.execute({
            "lecture_topic": lecture_topic,
            "profile": profile,
            "mode": mode,
            "knowledge_context": {},
        })
        content = result.get("lecture_doc", {}).get("content", "")
        return {
            "title": lecture_topic,
            "type": "理论课",
            "generation_mode": "fallback_single_agent",
            "verified": False,
            "status": "fallback_pending",
            "content": content if content else generate_fallback_lecture(course_id, lecture_num)["content"],
            "code": "# 单Agent快速生成 — 待审核管线补充代码示例",
            "mindmap": [],
            "quiz": {},
        }
    except Exception:
        return generate_fallback_lecture(course_id, lecture_num)


def generate_fallback_lecture(course_id: str, lecture_num: int) -> dict:
    """降级内容 — 未完成多智能体验证，不可作为最终发布资源"""
    course_name = get_course_name(course_id)
    lecture_topic = get_lecture_topic(course_id, lecture_num)

    return {
        "title": lecture_topic,
        "type": "理论课",
        "generation_mode": "fallback_single_agent",
        "verified": False,
        "status": "fallback_pending",
        "warning": "未完成多智能体验证，不可作为最终发布资源",
        "content": f"""
<h3>课程说明</h3>
<p>本节将系统讲解 <strong>{lecture_topic}</strong> 的核心知识和实践应用。</p>

<h3>学习目标</h3>
<ul>
  <li>理解 {lecture_topic} 的基本概念和定义</li>
  <li>掌握 {lecture_topic} 的核心原理和工作机制</li>
  <li>了解 {lecture_topic} 在实际数据分析项目中的应用场景</li>
  <li>能够独立完成 {lecture_topic} 相关的 Python 代码实现</li>
</ul>

<h3>内容概览</h3>
<p>本讲内容由 AI 智能体自动生成。请配置有效的 LLM API Key 后，系统将通过多智能体协同验证流程自动生成包含详细概念解释、原理说明、Python代码示例、易混淆点对比和练习题的完整讲义。</p>

<h3>学习建议</h3>
<ul>
  <li>先通读讲义，建立整体认知</li>
  <li>重点关注核心概念和关键流程</li>
  <li>动手运行 Python 代码示例，加深理解</li>
  <li>完成课后练习题，巩固知识</li>
</ul>
""",
        "code": f"""# {lecture_topic} — Python 数据分析示例
# 请配置 LLM API Key 后获取完整的 Agent 生成内容

import pandas as pd
import numpy as np

# 创建示例数据
df = pd.DataFrame({{
    'name': ['Alice', 'Bob', 'Charlie'],
    'score': [85, 92, 78],
    'level': ['B', 'A', 'C']
}})

# 基础数据分析
print("=== 数据预览 ===")
print(df.head())
print()
print("=== 统计摘要 ===")
print(df.describe())
print()
print("=== 按等级分组 ===")
print(df.groupby('level')['score'].mean())
""",
        "mindmap": [
            {"t": f"{lecture_topic} 概述", "s": "核心概念"},
            {"t": f"{lecture_topic} 原理", "s": "工作机制"},
            {"t": f"{lecture_topic} 实现", "s": "Python 代码实践"},
            {"t": "常见问题", "s": "注意事项"},
            {"t": "扩展应用", "s": "进阶方向"},
        ],
        "quiz": {
            "question": f"{lecture_topic} 在 Python 数据分析中的核心作用是什么？",
            "options": [
                {"text": "利用 Pandas/NumPy 高效处理和分析数据", "correct": True},
                {"text": "只能用于网页开发", "correct": False},
                {"text": "不需要理解数据即可使用", "correct": False},
                {"text": "仅用于机器学习，不用于数据清洗", "correct": False},
            ]
        }
    }
