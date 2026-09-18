"""Agent orchestration routes."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import asyncio
from datetime import datetime

from ..agents.orchestrator import LearnWeaveOrchestrator
from ..agents.unified_orchestrator import get_unified_orchestrator
from ..agents.verification_orchestrator import get_verification_orchestrator
from ..schemas import AgentRunRequest
from ..core.event_bus import event_bus

router = APIRouter(prefix="/api/agents", tags=["agents"])

# 10-Agent 统一注册表 — 按比赛要求命名
_agent_states: dict[str, dict] = {
    # 诊断层
    "learner_profile":     {"id": "learner_profile",     "name": "LearnerProfileAgent",       "category": "diagnosis",   "status": "idle"},
    "knowledge_retrieval": {"id": "knowledge_retrieval", "name": "KnowledgeRetrievalAgent",   "category": "diagnosis",   "status": "idle"},
    # 编排层
    "orchestrator":        {"id": "orchestrator",        "name": "OrchestratorAgent",         "category": "orchestration","status": "idle"},
    # 生成层
    "doc":      {"id": "doc",      "name": "DocAgent",      "category": "generation", "status": "idle"},
    "code":     {"id": "code",     "name": "CodeAgent",     "category": "generation", "status": "idle"},
    "quiz":     {"id": "quiz",     "name": "QuizAgent",     "category": "generation", "status": "idle"},
    "mindmap":  {"id": "mindmap",  "name": "MindmapAgent",  "category": "generation", "status": "idle"},
    "reading":  {"id": "reading",  "name": "ReadingAgent",  "category": "generation", "status": "idle"},
    "video":    {"id": "video",    "name": "VideoAgent",    "category": "generation", "status": "idle"},
    # 审核层
    "professional_audit": {"id": "professional_audit", "name": "ProfessionalAuditAgent", "category": "audit",    "status": "idle"},
    # 修订层
    "fix":      {"id": "fix",      "name": "FixAgent",           "category": "revision",  "status": "idle"},
    # 反馈层
    "feedback": {"id": "feedback", "name": "FeedbackAgent",      "category": "feedback",  "status": "idle"},
    # 决策层
    "decision": {"id": "decision", "name": "DecisionAgent",      "category": "decision",  "status": "idle"},
}


def reset_agent_states():
    """重置所有 Agent 状态为 idle"""
    for a in _agent_states.values():
        a["status"] = "idle"
        a.pop("started_at", None)
        a.pop("result", None)


async def _agent_state_listener(event):
    """监听 EventBus 事件，更新 Agent 状态"""
    etype = event.type
    data = event.data

    if etype == "agent_start":
        agent_name = data.get("agent", "")
        # Agent 名称 → 注册 ID 映射
        name_map = {
            "ProfileAgent": "learner_profile",
            "KnowledgeRetrievalAgent": "knowledge_retrieval",
            "OrchestratorAgent": "orchestrator",
            "DocAgent": "doc",
            "CodeAgent": "code",
            "QuizAgent": "quiz",
            "MindmapAgent": "mindmap",
            "ReadingAgent": "reading",
            "VideoAgent": "video",
            "AuditAgent": "professional_audit",
            "FixAgent": "fix",
            "AssessmentAgent": "feedback",
            "PathPlanner": "decision",
        }
        aid = name_map.get(agent_name)
        if aid and aid in _agent_states:
            _agent_states[aid]["status"] = "running"
            _agent_states[aid]["started_at"] = datetime.now().isoformat()
            await event_bus.publish("agent_state_changed", {
                "agent_id": aid, "status": "running", "name": _agent_states[aid]["name"]
            }, source="agent-tracker")

    elif etype == "agent_done":
        agent_name = data.get("agent", "")
        name_map = {
            "ProfileAgent": "profile", "DocAgent": "doc", "MindmapAgent": "mindmap",
            "CodeAgent": "code", "QuizAgent": "quiz", "ReadingAgent": "reading",
            "VideoAgent": "video", "AuditAgent": "audit", "PathPlanner": "path",
        }
        aid = name_map.get(agent_name)
        if aid and aid in _agent_states:
            _agent_states[aid]["status"] = "success"
            _agent_states[aid]["result"] = data.get("status", "success")
            await event_bus.publish("agent_state_changed", {
                "agent_id": aid, "status": "success", "name": _agent_states[aid]["name"]
            }, source="agent-tracker")

    elif etype == "agent_error":
        agent_name = data.get("agent", "")
        name_map = {
            "ProfileAgent": "profile", "DocAgent": "doc", "MindmapAgent": "mindmap",
            "CodeAgent": "code", "QuizAgent": "quiz", "ReadingAgent": "reading",
            "VideoAgent": "video", "AuditAgent": "audit", "PathPlanner": "path",
        }
        aid = name_map.get(agent_name)
        if aid and aid in _agent_states:
            _agent_states[aid]["status"] = "error"
            _agent_states[aid]["error"] = data.get("error", "")
            await event_bus.publish("agent_state_changed", {
                "agent_id": aid, "status": "error", "name": _agent_states[aid]["name"]
            }, source="agent-tracker")

    elif etype == "pipeline_stage":
        stage = data.get("stage", "")
        await event_bus.publish("agent_state_changed", {
            "agent_id": "pipeline", "status": "stage_change", "stage": stage
        }, source="agent-tracker")


# 启动时注册监听器
event_bus.on("agent_start", _agent_state_listener)
event_bus.on("agent_done", _agent_state_listener)
event_bus.on("agent_error", _agent_state_listener)
event_bus.on("pipeline_stage", _agent_state_listener)


@router.get("/status")
async def agents_status():
    return {
        "agents": list(_agent_states.values()),
        "orchestrator": "ready",
    }


@router.get("/realtime")
async def get_realtime_status():
    """获取所有 Agent 的实时状态"""
    return {"agents": list(_agent_states.values()), "timestamp": datetime.now().isoformat()}


@router.post("/run")
async def run_agents(req: AgentRunRequest):
    """触发 Agent 编排运行，重置状态并通过 EventBus 实时推送"""
    reset_agent_states()
    await event_bus.publish("pipeline_stage", {"stage": "starting", "message": "开始多Agent协同编排"}, source="orchestrator")

    try:
        result = LearnWeaveOrchestrator().run(req.profile)
        await event_bus.publish("pipeline_stage", {"stage": "complete", "message": "编排完成"}, source="orchestrator")
        return result
    except Exception as e:
        import traceback
        await event_bus.publish("pipeline_stage", {"stage": "error", "message": str(e)}, source="orchestrator")
        return {
            "error": str(e),
            "detail": traceback.format_exc()[-500:],
            "learning_path": {},
            "resources": {},
            "tutoring": {"answer": f"编排器执行失败: {e}", "sources": [], "follow_up": []},
            "quiz": {"questions": [], "generated_by": "error"},
            "assessment": {"mastery": 0, "weak_points": [], "recommendations": []},
            "focus_topic": "",
            "done": False,
        }


@router.post("/run-unified")
async def run_unified_orchestrator(req: AgentRunRequest):
    """运行 UnifiedOrchestrator（7 Agent 并行），重置状态并通过 EventBus 推送"""
    reset_agent_states()
    await event_bus.publish("pipeline_stage", {"stage": "starting", "message": "7 Agent并行编排开始"}, source="orchestrator")

    try:
        orch = get_unified_orchestrator()
        await event_bus.publish("pipeline_stage", {"stage": "generating", "message": "知识库加载 + 7 Agent并行生成中"}, source="orchestrator")
        result = await orch.run(
            course_id=req.course_id or "python-data-analysis",
            lecture_num=req.lecture_num or 1,
            course_title=req.course_title or "Python数据分析实战",
            lecture_topic=req.lecture_topic or "Python环境搭建",
            profile=req.profile or {},
            mode=req.mode or "study",
        )
        await event_bus.publish("pipeline_stage", {"stage": "complete", "message": "7 Agent编排完成"}, source="orchestrator")
        return result
    except Exception as e:
        import traceback
        await event_bus.publish("pipeline_stage", {"stage": "error", "message": str(e)}, source="orchestrator")
        return {"error": str(e), "detail": traceback.format_exc()[-500:]}


@router.post("/run-verified")
async def run_verified_orchestrator(req: AgentRunRequest):
    """运行 VerificationOrchestrator（生成→审核→修正→复审→决策）"""
    reset_agent_states()
    await event_bus.publish("pipeline_stage", {"stage": "starting", "message": "验证编排开始"}, source="orchestrator")

    try:
        orch = get_verification_orchestrator()
        result = await orch.run(
            course_id=req.course_id or "python-data-analysis",
            lecture_num=req.lecture_num or 1,
            course_title=req.course_title or "Python数据分析实战",
            lecture_topic=req.lecture_topic or "Python环境搭建",
            profile=req.profile or {},
            mode=req.mode or "study",
        )
        await event_bus.publish("pipeline_stage", {"stage": "complete", "message": "验证编排完成"}, source="orchestrator")
        return result
    except Exception as e:
        import traceback
        await event_bus.publish("pipeline_stage", {"stage": "error", "message": str(e)}, source="orchestrator")
        return {"error": str(e), "detail": traceback.format_exc()[-500:]}


@router.post("/trigger-demo")
async def trigger_demo():
    """触发演示用的 Agent 编排（使用默认数据）"""
    reset_agent_states()

    async def _run_demo():
        await event_bus.publish("pipeline_stage", {"stage": "starting", "message": "开始多Agent协同编排"}, source="orchestrator")

        # 阶段1: 学情诊断
        await event_bus.publish("agent_start", {"agent": "ProfileAgent", "message": "开始分析学习者画像..."}, source="orchestrator")
        await asyncio.sleep(1.2)
        await event_bus.publish("agent_done", {"agent": "ProfileAgent", "status": "success"}, source="orchestrator")
        await event_bus.publish("pipeline_stage", {"stage": "diagnosis_done", "message": "学情诊断完成"}, source="orchestrator")

        # 阶段2: 并行知识生成
        await event_bus.publish("pipeline_stage", {"stage": "generating", "message": "5 Agent并行生成中"}, source="orchestrator")
        gen_agents = ["DocAgent", "CodeAgent", "QuizAgent", "ReadingAgent", "VideoAgent"]
        for ag in gen_agents:
            await event_bus.publish("agent_start", {"agent": ag, "message": f"开始生成..."}, source="orchestrator")
        await asyncio.sleep(1.5)
        for ag in gen_agents:
            await event_bus.publish("agent_done", {"agent": ag, "status": "success"}, source="orchestrator")
        await event_bus.publish("pipeline_stage", {"stage": "generation_done", "message": "知识生成完成"}, source="orchestrator")

        # 导图在讲义之后
        await event_bus.publish("agent_start", {"agent": "MindmapAgent", "message": "基于讲义生成思维导图..."}, source="orchestrator")
        await asyncio.sleep(0.8)
        await event_bus.publish("agent_done", {"agent": "MindmapAgent", "status": "success"}, source="orchestrator")

        # 阶段3: 交叉验证
        await event_bus.publish("pipeline_stage", {"stage": "auditing", "message": "AuditAgent交叉验证中"}, source="orchestrator")
        await event_bus.publish("agent_start", {"agent": "AuditAgent", "message": "审核生成内容的准确性..."}, source="orchestrator")
        await asyncio.sleep(1.0)
        await event_bus.publish("agent_done", {"agent": "AuditAgent", "status": "success"}, source="orchestrator")
        await event_bus.publish("pipeline_stage", {"stage": "audit_done", "message": "审核完成，置信度94.2%"}, source="orchestrator")

        # 阶段4: 路径规划
        await event_bus.publish("pipeline_stage", {"stage": "planning", "message": "PathPlanner规划学习路径"}, source="orchestrator")
        await event_bus.publish("agent_start", {"agent": "PathPlanner", "message": "根据画像规划个性化路径..."}, source="orchestrator")
        await asyncio.sleep(0.6)
        await event_bus.publish("agent_done", {"agent": "PathPlanner", "status": "success"}, source="orchestrator")
        await event_bus.publish("pipeline_stage", {"stage": "complete", "message": "全流程执行完成"}, source="orchestrator")

    asyncio.create_task(_run_demo())
    return {"message": "Demo pipeline started", "status": "running"}
