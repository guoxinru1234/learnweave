"""LearnWeave API application."""
import sys, io
# Fix Windows GBK console encoding for emoji characters
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import os
import json as json_mod
import traceback

from .core.config import settings
from .core.database import init_db

# ===== 导入路由模块 =====
from .routers import agents, assessment, chat, generation, knowledge, labs, profile, quiz
from .routers import courses
from .routers.learning_records import router as learning_records_router
from .routers.daily_tasks import router as daily_tasks_router
from .routers.notes import router as notes_router
from .routers.lab_grader import router as lab_grader_router
from .routers.chat_history import router as chat_history_router
from .routers.journey import router as journey_router
from .routers.events import router as events_router
from .routers import auth
from .routers import admin
from .routers import user_profile
from .routers import video
from .routers import lecture
from .routers import learning  # 学习闭环:下一轮资源生成
from .routers import execute  # [OK] 只保留一次导入
from .routers import agent   # [OK] 新增 Agent 路由导入
from .routers import teacher  # 教师端路由
from .routers import verification  # 验证编排路由（挑战杯）
from .routers.interactions import router as interactions_router
from .routers.diagnosis import router as diagnosis_router
from .routers.evaluation import router as evaluation_router

# ===== 创建应用实例（必须放在 app.mount 之前） =====
app = FastAPI(title=settings.app_name, version=settings.version)

# ===== CORS 中间件 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 初始化数据库 =====
init_db()

# ===== 全局异常处理器 =====

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Pydantic 校验失败 → 422，返回可读的字段级错误。"""
    errors = []
    for err in exc.errors():
        loc = " → ".join(str(x) for x in err["loc"])
        errors.append({"field": loc, "message": err["msg"], "type": err["type"]})
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数校验失败",
            "errors": errors,
        },
    )



# ===== 挂载静态文件服务（视频） =====
os.makedirs("media/videos", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# ===== 注册路由（所有 include_router 放在这里） =====
app.include_router(knowledge.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(assessment.router)
app.include_router(labs.router)
app.include_router(generation.router)
app.include_router(agents.router)
app.include_router(courses.router)
app.include_router(learning_records_router)
app.include_router(daily_tasks_router)
app.include_router(notes_router)
app.include_router(lab_grader_router)
app.include_router(journey_router)
app.include_router(events_router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user_profile.router)
app.include_router(video.router)
app.include_router(lecture.router)
app.include_router(learning.router)  # 学习闭环:下一轮资源生成
app.include_router(execute.router)  # [OK] 注册执行路由
app.include_router(agent.router)    # [OK] 注册 Agent 路由
app.include_router(teacher.router)  # 教师端路由
app.include_router(verification.router)  # 验证编排路由（挑战杯）
app.include_router(interactions_router)  # 学习交互反馈
app.include_router(diagnosis_router)  # 学情诊断报告
app.include_router(evaluation_router)  # 质量评测报告

# ===== 启动事件 =====
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化智能体"""
    print("[INFO] LearnWeave 应用启动中...")

    try:
        from .agents.orchestrator_agent import get_orchestrator
        orchestrator = get_orchestrator()
        print("[INFO] 协调智能体已初始化并订阅事件")

        from .agents.assessment_agent import get_assessment_agent
        assessment_agent = get_assessment_agent()
        print("[INFO] 评估智能体已初始化并订阅事件")

        from .agents.path_planner_agent import get_path_planner
        path_planner = get_path_planner()
        print("[INFO] 路径规划智能体已初始化并订阅事件")

        from .agents.next_round import get_next_round_coordinator
        coordinator = get_next_round_coordinator()
        print("[INFO] 下一轮学习协调器已初始化并订阅事件")

        print("[OK] 所有智能体已就绪!")
    except ImportError as e:
        print(f"[WARN] 智能体初始化警告(部分功能可能受限): {e}")
    except Exception as e:
        print(f"[ERROR] 智能体初始化失败: {e}")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.version, "database": "ok"}


# ===== 课程元数据 API =====

@app.get("/api/courses")
async def api_list_courses():
    """列出所有可用课程。"""
    from .routers.lecture import list_courses as _list_courses
    courses = _list_courses()
    return {"success": True, "courses": courses}


@app.get("/api/courses/{course_id}")
async def api_get_course(course_id: str):
    """获取课程完整元数据（模块、讲次、Manim 映射等）。"""
    from .routers.lecture import get_course_metadata as _get_course
    course = _get_course(course_id)
    if course is None:
        return {"success": False, "message": f"课程 {course_id} 不存在"}
    return {"success": True, "course": course}
from .routers.community import router as community_router
app.include_router(community_router)
