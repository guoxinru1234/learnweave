"""视频生成 API — 真实 TTS 配音 + 分镜渲染管道

替代旧的 mock 实现。生成流程:
  1. PlannerAgent 生成分镜脚本
  2. TTSService 批量合成场景配音
  3. video_renderer_audio 合成最终 MP4
  4. SSE 流式推送进度
"""
import os
import json
import asyncio
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/video", tags=["video"])


class VideoGenerateRequest(BaseModel):
    lecture_title: str
    key_concepts: list[str] = []
    course_id: str = "python-data-analysis"
    lecture_num: int = 1
    difficulty: str = "medium"
    lecture_content: dict = None  # 可选的完整讲义内容


class VideoGenerateResponse(BaseModel):
    success: bool
    video_url: str
    score: float = 8.5
    duration: float = 0
    scenes_count: int = 0
    has_audio: bool = False
    message: str = ""


@router.post("/generate")
async def generate_video(request: VideoGenerateRequest):
    """真实视频生成 — TTS 配音 + 分镜渲染"""
    try:
        print(f"\n[VideoAPI] Generating video: {request.lecture_title}")
    except UnicodeEncodeError:
        print(f"\n[VideoAPI] Generating video (title omitted)")

    # 1. 准备讲义数据 — 优先从缓存加载完整课程内容
    lecture_data = request.lecture_content
    if not lecture_data:
        import glob
        cache_file = os.path.join("data", "lecture_cache", f"{request.course_id}_{request.lecture_num}.json")
        # 精确文件名找不到时，回退匹配带路径/hash 后缀的缓存，如 python_2_u2_path_2_xxx.json
        if not os.path.exists(cache_file):
            candidates = sorted(glob.glob(os.path.join(
                "data", "lecture_cache",
                f"{request.course_id}_{request.lecture_num}_*.json")))
            if candidates:
                cache_file = candidates[0]
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                # Convert cache format to planner format
                html_content = cached.get("content", "")
                # Strip HTML tags to get plain text
                import re
                plain_text = re.sub(r'<[^>]+>', '', html_content)
                # Extract key concepts and build structured content
                title = cached.get("title", request.lecture_title)
                key_concepts_list = request.key_concepts or []
                # Split text into sections
                paragraphs = [p.strip() for p in plain_text.split('\n') if len(p.strip()) > 10]
                lecture_data = {
                    "title": title,
                    "content": {
                        "introduction": paragraphs[0] if paragraphs else f"欢迎学习 {title}",
                        "core_knowledge": {
                            "concept": "。".join(paragraphs[1:5]) if len(paragraphs) > 1 else "。".join(key_concepts_list),
                            "principles": paragraphs[2] if len(paragraphs) > 2 else "",
                            "steps": paragraphs[3:6] if len(paragraphs) > 3 else [],
                            "example": paragraphs[6] if len(paragraphs) > 6 else "",
                        },
                        "key_points": key_concepts_list[:4] if key_concepts_list else (paragraphs[1:3] if len(paragraphs) > 1 else []),
                        "confusion_points": {"point": "", "takeaway": ""},
                        "summary": paragraphs[-1] if paragraphs else "",
                    },
                }
                print(f"  Loaded lecture cache: {len(paragraphs)} paragraphs")
            except Exception as e:
                print(f"  Cache load failed: {e}")
                pass
    if not lecture_data:
        lecture_data = {
            "title": request.lecture_title,
            "content": {
                "introduction": f"欢迎学习 {request.lecture_title}",
                "core_knowledge": {
                    "concept": "。".join(request.key_concepts) if request.key_concepts else request.lecture_title,
                },
            },
        }

    # 2. 生成分镜脚本
    from ..agents.planner_agent import PlannerAgent
    planner = PlannerAgent()

    # 在 executor 中运行同步 LLM 调用
    loop = asyncio.get_event_loop()
    script = await loop.run_in_executor(
        None, planner.generate_script, lecture_data, request.difficulty
    )
    scenes = script.get("scenes", [])
    try:
        print(f"  Script generated: {len(scenes)} scenes")
    except UnicodeEncodeError:
        print(f"  Script generated: {len(scenes)} scenes (text omitted)")

    # 3. TTS 配音合成
    from ..services.tts_service import get_tts_service
    tts = get_tts_service()

    dest_dir = os.path.join("media", "videos")
    os.makedirs(dest_dir, exist_ok=True)
    audio_dir = os.path.join(dest_dir, "audio", f"{request.course_id}_{request.lecture_num}")
    os.makedirs(audio_dir, exist_ok=True)

    audio_segments = await tts.synthesize_scenes(scenes, audio_dir)

    # 4. 渲染视频 + 配音合成
    from ..core.video_renderer_audio import render_video_with_audio
    filename = f"{request.course_id}_{request.lecture_num}.mp4"
    output_path = os.path.join(dest_dir, filename)

    video_path = await loop.run_in_executor(
        None,
        lambda: render_video_with_audio(scenes, audio_segments, output_path)
    )

    # 5. 计算时长
    total_duration = sum(s.get("duration", 3) for s in scenes)

    try:
        print(f"  Video generation complete: {video_path}")
    except UnicodeEncodeError:
        print(f"  Video generation complete (path omitted)")

    return VideoGenerateResponse(
        success=True,
        video_url=f"/media/videos/{filename}",
        score=8.5,
        duration=total_duration,
        scenes_count=len(scenes),
        has_audio=len(audio_segments) > 0,
        message=f"视频生成成功: {len(scenes)}个场景, {len(audio_segments)}段配音"
    )


@router.get("/generate-stream")
async def generate_video_stream(
    lecture_title: str,
    course_id: str = "python-data-analysis",
    lecture_num: int = 1,
    difficulty: str = "medium",
):
    """SSE 流式视频生成 — 实时推送进度"""
    async def event_generator():
        yield f"data: {json.dumps({'type': 'start', 'message': f'开始生成: {lecture_title}'})}\n\n"

        # Step 1: 规划分镜
        yield f"data: {json.dumps({'type': 'progress', 'step': 'planning', 'message': '正在规划分镜脚本...'})}\n\n"
        await asyncio.sleep(0.5)

        from ..agents.planner_agent import PlannerAgent
        planner = PlannerAgent()
        lecture_data = {"title": lecture_title, "content": {}}

        loop = asyncio.get_event_loop()
        script = await loop.run_in_executor(
            None, planner.generate_script, lecture_data, difficulty
        )
        scenes = script.get("scenes", [])
        yield f"data: {json.dumps({'type': 'progress', 'step': 'planning', 'scenes': len(scenes), 'message': f'分镜规划完成: {len(scenes)} 个场景'})}\n\n"

        # Step 2: TTS 配音
        yield f"data: {json.dumps({'type': 'progress', 'step': 'tts', 'message': '正在合成配音...', 'total': len(scenes)})}\n\n"
        await asyncio.sleep(0.3)

        from ..services.tts_service import get_tts_service
        tts = get_tts_service()
        audio_dir = os.path.join("media", "videos", "audio", f"{course_id}_{lecture_num}")
        os.makedirs(audio_dir, exist_ok=True)

        for i, scene in enumerate(scenes):
            voiceover = scene.get("voiceover", scene.get("text", ""))
            if voiceover:
                audio_path = os.path.join(audio_dir, f"scene_{i+1:02d}.mp3")
                await tts.synthesize(voiceover, output_path=audio_path)
                yield f"data: {json.dumps({'type': 'progress', 'step': 'tts', 'current': i+1, 'total': len(scenes), 'message': f'配音合成: {i+1}/{len(scenes)}'})}\n\n"

        # Step 3: 渲染
        yield f"data: {json.dumps({'type': 'progress', 'step': 'render', 'message': '正在渲染视频...'})}\n\n"
        await asyncio.sleep(0.3)

        dest_dir = os.path.join("media", "videos")
        os.makedirs(dest_dir, exist_ok=True)
        filename = f"{course_id}_{lecture_num}.mp4"
        output_path = os.path.join(dest_dir, filename)

        # 收集配音片段
        audio_segments = []
        for i, scene in enumerate(scenes):
            audio_path = os.path.join(audio_dir, f"scene_{i+1:02d}.mp3")
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                audio_segments.append({
                    "scene_index": i,
                    "audio_path": audio_path,
                    "duration": scene.get("duration", 3),
                })

        from ..core.video_renderer_audio import render_video_with_audio
        video_path = await loop.run_in_executor(
            None,
            lambda: render_video_with_audio(scenes, audio_segments, output_path)
        )

        # Step 4: 完成
        yield f"data: {json.dumps({'type': 'complete', 'video_url': f'/media/videos/{filename}', 'scenes': len(scenes), 'duration': sum(s.get('duration', 3) for s in scenes), 'message': '视频生成完成!'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/check/{course_id}/{lecture_num}")
def check_video_exists(course_id: str, lecture_num: int):
    """检查视频是否已生成"""
    filename = f"{course_id}_{lecture_num}.mp4"
    filepath = os.path.join("media", "videos", filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return {
            "exists": True,
            "video_url": f"/media/videos/{filename}",
            "file_size_kb": os.path.getsize(filepath) // 1024,
        }
    return {"exists": False}


@router.get("/demo")
async def generate_demo_video():
    """快速生成演示视频（测试用）"""
    return await generate_video(VideoGenerateRequest(
        lecture_title="Pandas 数据处理与分组聚合",
        key_concepts=["groupby 聚合", "数据透视表", "链式操作"],
        course_id="python-data-analysis",
        lecture_num=8,
    ))


class OrchestratedVideoRequest(BaseModel):
    """多Agent协同视频生成请求 — 使用完整 VideoOrchestrator 流水线"""
    lecture_title: str
    lecture_data: dict = None
    key_concepts: list[str] = []
    difficulty: str = "medium"
    profile: dict = None
    use_digital_human: bool = True
    use_manim: bool = True


@router.post("/generate-orchestrated")
async def generate_video_orchestrated(request: OrchestratedVideoRequest):
    """
    多Agent协同视频生成（赛题完整版）

    流水线: PlannerAgent → CoderAgent → CriticAgent(质量评审+迭代)
            → XFYunVideoAgent(数字人优先) / LocalRender(Manim+TTS配音)

    通过 SSE 实时推送进度 (/api/video/progress-stream)
    """
    from ..agents.video_orchestrator import get_video_orchestrator

    orchestrator = get_video_orchestrator()

    # Load lecture cache if available
    lecture_data = request.lecture_data
    if not lecture_data:
        cache_file = os.path.join("data", "lecture_cache", f"python-data-analysis_1.json")
        if os.path.exists(cache_file):
            import json as json_mod
            with open(cache_file, 'r', encoding='utf-8') as f:
                lecture_data = json_mod.load(f)

    result = await orchestrator.generate_video_async(
        lecture_title=request.lecture_title,
        lecture_data=lecture_data,
        key_concepts=request.key_concepts,
        difficulty=request.difficulty,
        profile=request.profile,
        use_digital_human=request.use_digital_human,
        use_manim=request.use_manim,
    )

    # Emit completion event
    from ..core.event_bus import event_bus
    event_bus.publish("video_generation_complete", {
        "title": request.lecture_title,
        "method": result.get("method", "unknown"),
        "score": result.get("final_score", 0),
    })

    return {
        "success": result.get("video_path") is not None,
        "video_url": result.get("video_path"),
        "script": result.get("script", {}),
        "method": result.get("method"),
        "final_score": result.get("final_score"),
        "passed": result.get("passed"),
        "iterations": result.get("iterations", []),
        "agent_logs": result.get("agent_logs", []),
        "scene_count": result.get("scene_count", 0),
        "message": f"生成完成: {result.get('method', 'unknown')} 方式, 质量评分 {result.get('final_score', 0):.1f}",
    }


@router.get("/progress-stream")
async def video_progress_stream():
    """
    SSE 流式推送 — 实时展示多Agent协作进度

    事件类型:
    - agent_status: {agent, status, message}
    - quality_check: {iteration, score, passed, feedback}
    - render_progress: {step, message}
    - complete: {video_url, method, score}
    """
    import asyncio as aio

    async def progress_generator():
        from ..core.event_bus import event_bus

        # Create a queue for this client
        queue = aio.Queue()

        async def on_agent_event(event):
            await queue.put({"type": "agent_status", "data": event})

        # Subscribe to agent events
        event_bus.on("*", on_agent_event)

        try:
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Agent monitor connected'})}\n\n"

            while True:
                try:
                    msg = await aio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(msg)}\n\n"
                except aio.TimeoutError:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.off("*", on_agent_event)

    return StreamingResponse(
        progress_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/agents-status")
async def get_agents_status():
    """获取所有Agent状态"""
    return {
        "agents": [
            {"id": "profile", "name": "画像分析Agent", "status": "ready", "description": "6维度学生画像构建"},
            {"id": "doc", "name": "文档生成Agent", "status": "ready", "description": "个性化讲义Markdown生成"},
            {"id": "mindmap", "name": "思维导图Agent", "status": "ready", "description": "知识点思维导图JSON生成"},
            {"id": "quiz", "name": "题库Agent", "status": "ready", "description": "练习题生成(选择/填空/编程)"},
            {"id": "code", "name": "代码Agent", "status": "ready", "description": "Python数据分析实操案例生成"},
            {"id": "reading", "name": "拓展阅读Agent", "status": "ready", "description": "扩展学习材料推荐"},
            {"id": "video", "name": "视频Agent", "status": "ready", "description": "教学视频分镜+渲染"},
            {"id": "manim", "name": "Manim动画Agent", "status": "ready", "description": "LLM驱动算法动画生成"},
            {"id": "path_planner", "name": "路径规划Agent", "status": "ready", "description": "个性化学习路径规划"},
            {"id": "orchestrator", "name": "统一编排器", "status": "ready", "description": "7Agent并行协调(LangGraph)"},
            {"id": "video_orchestrator", "name": "视频编排器", "status": "ready", "description": "Planner→Coder→Critic→Render"},
            {"id": "tutor", "name": "辅导Agent", "status": "ready", "description": "RAG+LLM智能答疑"},
            {"id": "assessment", "name": "评估Agent", "status": "ready", "description": "学习效果动态评估"},
        ],
        "llm_provider": os.getenv("LLM_PROVIDER", "xfyun"),
        "tts_available": bool(os.getenv("XFYUN_TTS_APP_ID", "")),
        "vms_available": bool(os.getenv("XFYUN_VMS_APP_ID", "")),
    }


@router.get("/manim/{course_id}/{lecture_num}")
async def generate_manim_animation(
    course_id: str,
    lecture_num: int,
    profile_json: str = None,
):
    """LLM 驱动生成个性化 Manim 教学动画 —— 赛题核心功能"""
    from ..agents.manim_agent import ManimAgent

    # Load lecture content
    import json as json_mod
    cache_file = os.path.join("data", "lecture_cache", f"{course_id}_{lecture_num}.json")
    lecture_doc = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                lecture_doc = json_mod.load(f)
        except Exception:
            pass

    profile = {}
    if profile_json:
        try:
            profile = json_mod.loads(profile_json)
        except Exception:
            pass

    topic = lecture_doc.get("title", f"Lecture {lecture_num}")
    agent = ManimAgent()
    result = await agent.execute({
        "lecture_topic": topic,
        "lecture_doc": lecture_doc,
        "profile": profile,
        "mode": "study",
    })

    if result.get("manim_video"):
        return {
            "success": True,
            "video_url": f"/media/videos/manim_{agent._safe_name(topic)}.mp4",
            "generation_method": "llm_manim",
            "personalized": bool(profile),
        }
    return {"success": False, "message": "Manim generation failed"}


# ========== 数字人实时推流（讯飞VMS → RTMP → HLS） ==========

_digital_human_state = {"running": False, "hls_url": None, "session": None}


class DigitalHumanRequest(BaseModel):
    text: str = "同学们好，欢迎来到LearnWeave智能学习平台。我是你们的AI教师。"


@router.post("/digital-human/start")
async def start_digital_human(req: DigitalHumanRequest):
    """启动数字人实时推流：VMS → RTMP → ffmpeg HLS → 返回播放URL"""
    import subprocess, shutil, time, base64 as b64, hashlib, hmac, ssl as ssl_mod, urllib.request as urlreq, urllib.error

    global _digital_human_state
    if _digital_human_state.get("running"):
        return {"success": True, "hls_url": _digital_human_state["hls_url"], "message": "已运行中"}

    app_id = os.getenv("XFYUN_VMS_APP_ID", "")
    api_key = os.getenv("XFYUN_VMS_API_KEY", "")
    api_secret = os.getenv("XFYUN_VMS_API_SECRET", "")
    if not all([app_id, api_key, api_secret]):
        return {"success": False, "message": "VMS凭证未配置"}

    host = "vms.cn-huadong-1.xf-yun.com"
    ctx_ssl = ssl_mod.create_default_context()

    def vms_auth(path):
        now = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime())
        sig_origin = f'host: {host}\ndate: {now}\nPOST {path} HTTP/1.1'
        sig = b64.b64encode(hmac.new(api_secret.encode(), sig_origin.encode(), hashlib.sha256).digest()).decode()
        auth = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig}"'
        return {'Content-Type': 'application/json', 'Host': host, 'Date': now, 'Authorization': auth}

    def vms_post(path, data):
        body = json.dumps(data).encode()
        headers = vms_auth(path)
        req = urlreq.Request(f'https://{host}{path}', data=body, headers=headers, method='POST')
        try:
            with urlreq.urlopen(req, timeout=20, context=ctx_ssl) as r:
                return json.loads(r.read().decode())
        except urlreq.HTTPError as e:
            return {"_err": e.code, "_body": e.read().decode('utf-8', errors='replace')[:200]}
        except Exception as e:
            return {"_err": str(e)}

    # Step 1: Start VMS with RTMP (retry up to 6 times, VMS has 1路并发)
    loop = asyncio.get_event_loop()
    start_resp = None
    for attempt in range(6):
        start_resp = await loop.run_in_executor(None, lambda: vms_post('/v1/private/vms2d_start', {
            'header': {'app_id': app_id},
            'parameter': {'vmr': {
                'avatar_id': '110017006', 'width': 1280, 'height': 720,
                'stream': {'protocol': 'rtmp'}
            }},
        }))
        if '_err' not in start_resp:
            break
        err_body = start_resp.get('_body', '')
        if '11203' in str(err_body):
            print(f"[DH] VMS slot busy, retry {attempt+1}/6...")
            await asyncio.sleep(8)  # Wait for previous session to expire
        else:
            return {"success": False, "message": f"VMS启动失败: {start_resp.get('_body', start_resp.get('_err'))[:200]}"}

    if '_err' in start_resp:
        return {"success": False, "message": "VMS会话获取失败，请等待30秒后重试"}

    session = start_resp['header']['session']
    rtmp_url = start_resp['header']['stream_url']
    print(f"[DH] Session={session[:30]}... RTMP={rtmp_url[:50]}...")

    # Step 2: Start ffmpeg FIRST (listen for stream before driving avatar)
    hls_dir = os.path.join("media", "hls")
    os.makedirs(hls_dir, exist_ok=True)
    for f in list(os.listdir(hls_dir)):
        try: os.remove(os.path.join(hls_dir, f))
        except: pass

    ffmpeg_exe = shutil.which("ffmpeg") or r"D:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
    if not os.path.exists(ffmpeg_exe):
        return {"success": False, "message": "ffmpeg未安装"}

    proc = subprocess.Popen([
        ffmpeg_exe, '-y', '-i', rtmp_url,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-c:a', 'aac', '-ar', '44100', '-ac', '1',
        '-f', 'hls', '-hls_time', '2', '-hls_list_size', '10',
        '-hls_flags', 'delete_segments+append_list',
        os.path.join(hls_dir, 'live.m3u8')
    ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    print(f"[DH] ffmpeg PID={proc.pid}")

    # Step 3: Drive avatar (ffmpeg is already listening)
    text_b64 = b64.b64encode(req.text.encode()).decode()
    drive_resp = await loop.run_in_executor(None, lambda: vms_post('/v1/private/vms2d_ctrl', {
        'header': {'app_id': app_id, 'session': session},
        'parameter': {},
        'payload': {'text': {'encoding': 'utf8', 'text': text_b64}},
    }))
    if '_err' in drive_resp:
        proc.terminate()
        return {"success": False, "message": f"数字人驱动失败: {drive_resp.get('_body', drive_resp.get('_err'))[:200]}"}
    print(f"[DH] Drive OK, waiting for HLS...")

    # Step 4: Wait for first HLS segment
    m3u8_path = os.path.join(hls_dir, 'live.m3u8')
    for _ in range(20):
        await asyncio.sleep(0.5)
        if os.path.exists(m3u8_path) and os.path.getsize(m3u8_path) > 50:
            break
        # Check if ffmpeg crashed
        if proc.poll() is not None:
            stderr = proc.stderr.read().decode('utf-8', errors='replace')[-300:] if proc.stderr else ''
            print(f"[DH] ffmpeg crashed: {stderr}")
            return {"success": False, "message": f"ffmpeg异常退出: {stderr[:200]}"}

    if not os.path.exists(m3u8_path) or os.path.getsize(m3u8_path) < 50:
        proc.terminate()
        return {"success": False, "message": "HLS转码启动失败，请重试"}

    _digital_human_state = {
        "running": True,
        "hls_url": "/media/hls/live.m3u8",
        "session": session,
        "proc": proc,
    }
    return {
        "success": True,
        "hls_url": "/media/hls/live.m3u8",
        "message": f"数字人已启动，正在讲解...",
    }


@router.get("/digital-human/stop")
async def stop_digital_human():
    """停止数字人"""
    global _digital_human_state
    proc = _digital_human_state.get("proc")
    if proc:
        proc.terminate()
        try: proc.wait(timeout=3)
        except: proc.kill()
    _digital_human_state = {"running": False, "hls_url": None, "session": None}
    return {"success": True, "message": "数字人已停止"}


@router.get("/digital-human/status")
async def digital_human_status():
    """获取数字人状态"""
    return {
        "running": _digital_human_state["running"],
        "hls_url": _digital_human_state.get("hls_url"),
    }
