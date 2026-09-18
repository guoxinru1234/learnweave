"""
OrchestratorAgent — 根据学情诊断结果和知识证据动态调度 Agent。

调度规则:
  1. 基础薄弱(均分<35): 讲义 + 分步代码 + 基础题，难度 basic
  2. 理论强实操弱: 减少基础讲解，增加实操(代码+实验)，无 video
  3. 高掌握度(均分≥70): 进阶任务，难度 advanced
  4. 知识库证据不足: 标记人工确认
  5. 有明确学习目标时围绕目标选择资源类型
"""
import uuid
from typing import List, Dict, Any


class OrchestratorAgent:
    """协调智能体 — 根据诊断结果动态调度 Agent，不固定调用全部 Agent。"""

    def __init__(self):
        self.name = "OrchestratorAgent"

    def create_dispatch_plan(
        self,
        learner_diagnosis: Dict[str, Any] = None,
        retrieved_evidence: List[Dict[str, Any]] = None,
        learning_goal: str = "",
        requested_resource_types: List[str] = None,
    ) -> dict:
        """
        根据学情诊断和知识证据，生成选择性的 Agent 调度计划。

        输出包含 selected_agents（仅选中需要的Agent），难度分级，
        以及证据不足时的 fallback 方案。
        """
        diagnosis = learner_diagnosis or {}
        evidence = retrieved_evidence or []
        requested = requested_resource_types or []

        # 从诊断中提取关键指标
        scores = diagnosis.get("mastery_scores", {})
        if not scores:
            scores = {
                "theoretical_basis": diagnosis.get("theoretical_basis", 30),
                "coding_ability": diagnosis.get("coding_ability", 30),
                "practical_ops": diagnosis.get("practical_ops", 30),
                "troubleshooting": diagnosis.get("troubleshooting", 30),
                "data_thinking": diagnosis.get("data_thinking", 30),
                "self_learning": diagnosis.get("self_learning", 30),
            }
        level = diagnosis.get("learner_level", "beginner")
        overall = diagnosis.get("overall_score", sum(scores.values()) // max(len(scores), 1))
        gaps = diagnosis.get("knowledge_gaps", [])
        mastered = diagnosis.get("mastered_points", [])

        # 核心规则
        theo = scores.get("theoretical_basis", 30)
        code = scores.get("coding_ability", 30)
        prac = scores.get("practical_ops", 30)
        evidence_count = len(evidence)
        evidence_insufficient = evidence_count < 2
        goal = learning_goal or diagnosis.get("learning_goal", "")

        # 难度判定
        if overall < 35:
            difficulty = "basic"
        elif overall < 70:
            difficulty = "intermediate"
        else:
            difficulty = "advanced"

        # 目标知识点
        target_kp = [g["knowledge_point"] for g in gaps[:3]] if gaps else ["Python 基础", "数据分析入门"]

        # ---- 调度规则 ----
        selected: list = []
        evidence_req: list = []

        # 规则1: 基础薄弱 → 讲义 + 代码 + 基础题
        if overall < 35:
            selected.append({"agent_name": "DocAgent", "priority": 1, "reason": "基础薄弱，需系统讲解", "difficulty": "basic", "evidence_required": True})
            selected.append({"agent_name": "CodeAgent", "priority": 1, "reason": "需要分步代码示例", "difficulty": "basic", "evidence_required": True})
            selected.append({"agent_name": "QuizAgent", "priority": 1, "reason": "基础题巩固理解", "difficulty": "basic", "evidence_required": False})
            if "数据" in str(gaps) or prac < 40:
                selected.append({"agent_name": "ReadingAgent", "priority": 3, "reason": "补充阅读材料", "difficulty": "basic", "evidence_required": False})
            # 基础阶段不生成视频，聚焦文字+代码
        # 规则2: 理论强但实操弱
        elif theo >= 60 and prac < 40:
            selected.append({"agent_name": "DocAgent", "priority": 2, "reason": "理论基础好，简要回顾即可", "difficulty": "intermediate", "evidence_required": True})
            selected.append({"agent_name": "CodeAgent", "priority": 1, "reason": "重点加强实操编程", "difficulty": "intermediate", "evidence_required": True})
            selected.append({"agent_name": "QuizAgent", "priority": 2, "reason": "侧重排错和实操题", "difficulty": "intermediate", "evidence_required": False})
            # 不选 VideoAgent — 实操阶段不需要视频
        # 规则3: 高掌握度 → 进阶
        elif overall >= 70:
            selected.append({"agent_name": "DocAgent", "priority": 2, "reason": "仅需补充进阶内容", "difficulty": "advanced", "evidence_required": True})
            selected.append({"agent_name": "CodeAgent", "priority": 2, "reason": "进阶代码挑战", "difficulty": "advanced", "evidence_required": True})
            selected.append({"agent_name": "QuizAgent", "priority": 1, "reason": "进阶综合题", "difficulty": "advanced", "evidence_required": False})
            selected.append({"agent_name": "ReadingAgent", "priority": 2, "reason": "拓展阅读", "difficulty": "advanced", "evidence_required": False})
            if len(mastered) >= 4:
                selected.append({"agent_name": "VideoAgent", "priority": 3, "reason": "可选视频总结", "difficulty": "advanced", "evidence_required": False})
        # 默认: 均衡
        else:
            selected.append({"agent_name": "DocAgent", "priority": 1, "reason": "均衡发展", "difficulty": difficulty, "evidence_required": True})
            selected.append({"agent_name": "CodeAgent", "priority": 1, "reason": "配合讲义练习", "difficulty": difficulty, "evidence_required": True})
            selected.append({"agent_name": "QuizAgent", "priority": 2, "reason": "检验理解", "difficulty": difficulty, "evidence_required": False})

        # 规则4: 有学习目标时过滤资源类型
        if goal and requested:
            goal_lower = goal.lower()
            if "就业" in goal_lower or "转行" in goal_lower:
                # 就业导向: 优先代码+项目
                selected = [a for a in selected if a["agent_name"] in ("CodeAgent", "DocAgent", "QuizAgent")]
                selected = sorted(selected, key=lambda x: 1 if x["agent_name"] == "CodeAgent" else 2)
            elif "竞赛" in goal_lower:
                selected = [a for a in selected if a["agent_name"] in ("CodeAgent", "QuizAgent", "ReadingAgent")]
                for a in selected:
                    a["difficulty"] = "advanced"
            elif "考研" in goal_lower:
                selected = [a for a in selected if a["agent_name"] in ("DocAgent", "QuizAgent")]

        # 过滤到 requested 类型
        if requested:
            req_set = set(r.lower().replace("agent", "") for r in requested)
            selected = [a for a in selected if a["agent_name"].lower().replace("agent", "") in req_set]

        # 规则5: 证据不足
        if evidence_insufficient:
            evidence_req = ["需人工确认或上传更多知识库资料"]
            if not any(a["agent_name"] == "DocAgent" and a["priority"] == 1 for a in selected):
                evidence_req.append("建议优先运行 KnowledgeRetrievalAgent 补充检索")

        # Fallback
        fallback = "若 selected_agents 中任一Agent生成失败，使用其同名静态模板降级，并标记 verified=false"

        return {
            "task_id": str(uuid.uuid4())[:12],
            "learner_level": level,
            "target_knowledge_points": target_kp,
            "selected_agents": selected,
            "dispatch_plan": f"根据{level}水平(均分{overall})、{len(gaps)}个薄弱点和{evidence_count}条证据，选择{len(selected)}个Agent",
            "difficulty": difficulty,
            "required_resource_types": list(set(a["agent_name"] for a in selected)),
            "evidence_requirements": evidence_req,
            "fallback_plan": fallback,
        }


def get_orchestrator() -> OrchestratorAgent:
    return OrchestratorAgent()
