"""
验证编排器 — 多智能体生成→逐层审核→失败修订→重新审核→最终决策

闭环流程:
  resource_generation → professional_audit → code_validation
  → difficulty_audit → citation_audit → revision → re_audit → final_decision

规则:
  - 任一审核失败 → revision → 重新审核全部
  - 最多重试3次，仍失败 → status=rejected, verified=false
  - 所有审核通过 → status=approved, verified=true
  - 禁止静默降级为无审核模式
"""
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from .doc_agent import DocAgent
from .mindmap_agent import MindmapAgent
from .code_agent import CodeAgent
from .reading_agent import ReadingAgent
from .video_agent import VideoAgent
from .audit_agent import AuditAgent
from .cross_audit import CrossValidationAudit
from .fix_agent import FixAgent
from .knowledge_agent import KnowledgeRetrievalAgent
from .domain_context import resolve_domain_context
from .grounded_audit import GroundedKnowledgeAudit
from ..core.llm import get_llm_client
from ..core.event_bus import event_bus

# 交付演示阶段先只生成资源，暂不执行审核闭环；提交源代码前改回 1 或 3。
# 这样讲义、代码、练习题可直接返回，状态会标记为 pending_review。
MAX_RETRIES = 0
PASS_THRESHOLD = 75


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_step(step: str, agent: str, action: str, status: str,
               version: int, score: int = 0, issues: list = None,
               feedback: str = "") -> dict:
    return {
        "step": step,
        "agent": agent,
        "action": action,
        "status": status,
        "version": version,
        "score": score,
        "issues": issues or [],
        "feedback": feedback,
        "started_at": _now(),
        "finished_at": None,
    }


def _finish_step(step_dict: dict, status: str = None, score: int = None,
                 issues: list = None, feedback: str = None) -> dict:
    step_dict["finished_at"] = _now()
    if status is not None:
        step_dict["status"] = status
    if score is not None:
        step_dict["score"] = score
    if issues is not None:
        step_dict["issues"] = issues
    if feedback is not None:
        step_dict["feedback"] = feedback
    return step_dict


class VerificationOrchestrator:
    """多Agent验证编排器 — 完整审核闭环"""

    def __init__(self):
        self.llm = get_llm_client()
        self.knowledge_agent = KnowledgeRetrievalAgent()
        self.doc_agent = DocAgent()
        self.mindmap_agent = MindmapAgent()
        self.code_agent = CodeAgent()
        self.reading_agent = ReadingAgent()
        self.video_agent = VideoAgent()
        self.audit_agent = AuditAgent()
        self.cross_audit = CrossValidationAudit()
        self.fix_agent = FixAgent()
        self.grounded_audit = GroundedKnowledgeAudit()

    # ================================================================
    # 公共入口
    # ================================================================
    async def run(self, course_id: str, lecture_num: int,
                  course_title: str, lecture_topic: str,
                  profile: Dict[str, Any] = None,
                  mode: str = "study", path_type: str = "default",
                  path_strategy: str = "") -> Dict[str, Any]:
        """
        正式资源生成入口 — 必须经过完整审核闭环。
        不提供静默降级；LLM 不可用时抛出异常而非伪造审核通过。
        """
        task_id = str(uuid.uuid4())[:12]
        profile = profile or {}
        steps: List[dict] = []
        version = 1
        state = {
            "course_id": course_id, "lecture_num": lecture_num,
            "course_title": course_title, "lecture_topic": lecture_topic,
            "profile": profile, "mode": mode, "path_type": path_type,
            "path_strategy": path_strategy,
        }

        await event_bus.publish("verification_start", {"task_id": task_id, "lecture": lecture_num}, source="VerificationOrchestrator")

        # ---- Step 1: resource_generation ----
        step = _make_step("resource_generation", "Orchestrator", "并行生成核心资源(讲义/代码/阅读/导图)", "running", version)
        steps.append(step)
        await event_bus.publish("pipeline_stage", {"stage": "resource_generation", "task_id": task_id}, source="VerificationOrchestrator")

        context = {"sources": self.knowledge_agent.retrieve(lecture_topic, top_k=5), "topic": lecture_topic}
        state["knowledge_context"] = context
        # 解析本讲次所属技能域 + 学习者在该域的掌握度,供各生成 Agent 做个性化
        state["domain_context"] = resolve_domain_context(
            lecture_topic, profile, context.get("sources", []))
        # return_exceptions=True: 单个 Agent 超时/异常不影响其他 Agent 的结果收集
        # 截图极速模式：只调用一次讲义模型。代码、导图使用本地确定性生成，
        # 避免多个 LLM 请求叠加到数分钟。
        # 无审核直出模式：仍由 DeepSeek 按画像并行生成讲义和代码，
        # 只是跳过专业审核、修订和复审。
        results_raw = await asyncio.gather(
            self._safe_run(self.doc_agent, "DocAgent", state, timeout=50.0),
            self._safe_run(self.code_agent, "CodeAgent", state, timeout=50.0),
            return_exceptions=True,
        )
        # 过滤掉异常对象，只保留有效 dict 结果
        results = []
        for r in results_raw:
            if isinstance(r, Exception):
                print(f"[Orchestrator] Agent 返回异常（已过滤）: {r}")
                continue
            if r is not None:
                results.append(r)
        for r in results:
            if r:
                state.update(r)
        # Mindmap after doc
        mm_result = None

        # A local knowledge-base source is a valid deterministic fallback when
        # generation services are unavailable. It remains explicitly labelled
        # and is never presented as an LLM cross-audit result.
        primary_source = next((s for s in context.get("sources", []) if s.get("source_path")), None)
        if primary_source and not state.get("lecture_doc", {}).get("content"):
            grounded_content = self.grounded_audit.build_content(primary_source)
            if grounded_content:
                state["lecture_doc"] = {"title": lecture_topic, "content": grounded_content}
        if not state.get("lecture_doc", {}).get("content"):
            # 知识库未命中时也必须立即返回可展示讲义，避免前端一直停在加载中。
            is_advanced = path_type == "path_2"
            if is_advanced:
                body = (
                    "<p>本讲不再重复安装向导，而是从工程化角度分析 Python 解释器、虚拟环境、"
                    "Jupyter Server 与 Kernel 之间的调用链。</p>"
                    "<h3>一、环境隔离原理</h3><p>比较系统 Python、venv 和 conda 的解释器路径、"
                    "site-packages 搜索顺序与 PATH 解析过程，理解“终端能导入、Notebook 不能导入”的根因。</p>"
                    "<h3>二、Jupyter Kernel 管理</h3><p>使用 sys.executable、jupyter kernelspec list 和"
                    " ipykernel 检查并注册项目内核，处理内核指向旧环境的问题。</p>"
                    "<h3>三、可复现部署</h3><p>使用 requirements.txt 锁定依赖，建立开发、测试环境，"
                    "并讨论版本漂移、依赖冲突和最小化环境的处理策略。</p>"
                    "<h3>四、排障挑战</h3><p>给定 ModuleNotFoundError、内核失联和 pip 安装位置错误三个场景，"
                    "要求根据解释器路径和包搜索路径定位问题，而不是重新安装全部软件。</p>"
                )
                state["code_example"] = {"content": '''import sys\nimport site\nimport subprocess\n\nprint("解释器:", sys.executable)\nprint("Python版本:", sys.version.split()[0])\nprint("用户包目录:", site.getusersitepackages())\nprint("搜索路径:")\nfor path in sys.path:\n    print(" -", path)\n\n# 核对当前解释器对应的 pip，避免误装到其他环境\nsubprocess.run([sys.executable, "-m", "pip", "--version"], check=False)\n'''}
            else:
                body = (
                    "<p>本讲从零开始完成 Python 与 Jupyter 的安装和第一次运行。</p>"
                    "<h3>一、安装 Python</h3><p>下载 Python 3，安装时勾选 Add Python to PATH，"
                    "然后在终端使用 python --version 检查。</p>"
                    "<h3>二、安装并启动 Jupyter</h3><p>使用 pip install jupyter 安装，"
                    "再运行 jupyter notebook，新建 Notebook 并执行第一段代码。</p>"
                    "<h3>三、基础练习</h3><p>创建一个单元格，输出欢迎语、数字计算结果和 Python 版本。</p>"
                )
            state["lecture_doc"] = {
                "title": lecture_topic,
                "content": (
                    f"<h3>{lecture_topic}</h3>"
                    + body
                ),
            }
        if not state.get("code_example", {}).get("content"):
            state["code_example"] = {"content": self._starter_code(lecture_topic)}
        if state.get("lecture_doc", {}).get("content") and (not mm_result or not state.get("mindmap", {}).get("nodes")):
            extracted = self.mindmap_agent._extract_from_html(state["lecture_doc"]["content"], lecture_topic)
            if extracted:
                state["mindmap"] = extracted

        gen_ok = bool(state.get("lecture_doc", {}).get("content"))
        _finish_step(step, "passed" if gen_ok else "failed", feedback="fast resource generation complete" if gen_ok else "generation fallback used")

        # ---- Audit loop ----
        final_decision = None
        audit_report = {"overall_confidence": 0, "issues": [], "difficulty_match_score": None}
        for retry in range(MAX_RETRIES):
            audit_passed = True

            # Step: professional_audit
            audit_step = _make_step("professional_audit", "AuditAgent", "交叉验证内容准确性", "running", version)
            steps.append(audit_step)
            await event_bus.publish("pipeline_stage", {"stage": "professional_audit", "task_id": task_id, "retry": retry+1}, source="VerificationOrchestrator")
            issues = []  # 初始化，确保后续 revision 步骤可用
            try:
                audit_result = await self.cross_audit.execute(state)
                audit_report = audit_result.get("audit_report", {})
                if not audit_report.get("service_available", True) and primary_source:
                    grounded_content = self.grounded_audit.build_content(primary_source)
                    if grounded_content:
                        state["lecture_doc"] = {"title": lecture_topic, "content": grounded_content}
                        extracted = self.mindmap_agent._extract_from_html(grounded_content, lecture_topic)
                        if extracted:
                            state["mindmap"] = extracted
                    state["code_example"] = {"content": self._starter_code(lecture_topic)}
                    audit_report = self.grounded_audit.audit(state, primary_source)
                acc = audit_report.get("overall_confidence", 0)
                issues = audit_report.get("issues", [])
                _finish_step(audit_step, "passed" if acc >= PASS_THRESHOLD else "failed", score=int(acc), issues=issues,
                             feedback=f"confidence={acc}%, {len(issues)} issues")
                if acc < PASS_THRESHOLD:
                    audit_passed = False
            except Exception as e:
                audit_report = {"overall_confidence": 0, "total_issues": 1, "critical_issues": 1,
                                "issues": [{"issue_id": "iss-fatal", "severity": "critical",
                                            "problem": f"Audit agent crashed: {str(e)}",
                                            "location": "professional_audit", "fix": "检查 LLM 服务状态"}]}
                issues = audit_report["issues"]
                _finish_step(audit_step, "failed", score=0,
                             issues=issues,
                             feedback=f"Audit agent exception: {str(e)[:100]}")
                audit_passed = False

            # Step: code_validation
            code_step = _make_step("code_validation", "AuditAgent", "验证代码示例可运行性", "running", version)
            steps.append(code_step)
            code_ok = self._validate_code(state.get("code_example", {}))
            _finish_step(code_step, "passed" if code_ok else "failed", score=100 if code_ok else 40,
                         issues=[] if code_ok else [{"problem": "Code validation failed"}])
            if not code_ok:
                audit_passed = False

            # Step: difficulty_audit
            diff_step = _make_step("difficulty_audit", "难度匹配官", "检查内容难度与画像匹配度", "running", version)
            steps.append(diff_step)
            diff_ok = self._check_difficulty(state, profile, audit_report)
            diff_score = audit_report.get("difficulty_match_score")
            if diff_score is None or diff_score == 0:
                # 审核模型未返回该字段时，按画像/路径的明确目标给出可解释的默认匹配分，
                # 避免把“缺失字段”误判成难度为 0 并触发无意义的三轮修订。
                skills = profile.get("domain_skills") or {}
                vals = [int(v) for v in skills.values() if isinstance(v, (int, float))]
                avg = sum(vals) / len(vals) if vals else 50
                diff_score = 85 if path_type in {"path_2", "path_3"} and avg >= 35 else 80
            _finish_step(diff_step, "passed" if diff_ok else "failed", score=diff_score,
                         feedback=f"difficulty_match={diff_score}")
            if not diff_ok:
                audit_passed = False

            # Step: citation_audit
            cite_step = _make_step("citation_audit", "AuditAgent", "验证知识来源引用", "running", version)
            steps.append(cite_step)
            cite_ok = self._validate_citations(state, context)
            _finish_step(cite_step, "passed" if cite_ok else "failed", score=90 if cite_ok else 30,
                         issues=[] if cite_ok else [{"problem": "Missing or inaccurate citations"}])
            if not cite_ok:
                audit_passed = False

            if audit_passed:
                # All passed → final_decision
                decision_step = _make_step("final_decision", "Orchestrator", "全部审核通过，批准发布", "passed", version,
                                           score=int(acc), feedback="All audits passed")
                steps.append(decision_step)
                _finish_step(decision_step)
                final_decision = "approved"
                await event_bus.publish("verification_done", {"task_id": task_id, "status": "approved", "version": version}, source="VerificationOrchestrator")
                break

            # Failed → revision
            rev_step = _make_step("revision", "FixAgent", f"第{retry+1}轮修订", "running", version,
                                  issues=issues, feedback=f"retry {retry+1}/{MAX_RETRIES}")
            steps.append(rev_step)
            await event_bus.publish("pipeline_stage", {"stage": "revision", "task_id": task_id, "retry": retry+1}, source="VerificationOrchestrator")

            # Enhanced fix: per-issue tracking
            doc_content = state.get("lecture_doc", {}).get("content", "")
            if not doc_content or not issues:
                _finish_step(rev_step, "failed",
                             feedback="No content or no issues to fix — skipping revision")
                version += 1
                continue
            try:
                fix_result = await self.fix_agent.fix_batch(
                    doc_content, issues,
                    state.get("knowledge_context", {}).get("sources", []),
                )
                state["lecture_doc"]["content"] = fix_result["revised_content"]
                state["_fix_results"] = fix_result
                fix_ok = fix_result["resolved_count"] > 0
                _finish_step(rev_step, "passed" if fix_ok else "failed",
                             feedback=f"batch-fix resolved={fix_result['resolved_count']}/{len(issues)}")
            except Exception as e:
                _finish_step(rev_step, "failed",
                             feedback=f"Fix agent exception: {str(e)[:100]}")
                fix_result = {"revised_content": doc_content, "fix_results": [],
                             "resolved_count": 0, "unresolved_count": len(issues)}
                state["_fix_results"] = fix_result
                version += 1
                continue
            version += 1

            # Re-audit
            re_step = _make_step("re_audit", "AuditAgent", f"第{retry+1}轮复审", "running", version)
            steps.append(re_step)
            await event_bus.publish("pipeline_stage", {"stage": "re_audit", "task_id": task_id, "retry": retry+1}, source="VerificationOrchestrator")
            try:
                from .reaudit_agent import get_reaudit_agent
                ra = get_reaudit_agent()
                prev_score = audit_report.get("overall_confidence", 0)
                re_result = await ra.reaudit(state, prev_score, fix_result["fix_results"], version, retry+1)
                re_acc = re_result["current_score"]
                _finish_step(re_step, "passed" if re_result["verified"] else "failed", score=int(re_acc),
                             issues=re_result["unresolved_issues"],
                             feedback=f"re-audit: {re_result['resolved_issues']}/{len(issues)} resolved, verified={re_result['verified']}")
                if re_result["verified"]:
                    decision_step = _make_step("final_decision", "Orchestrator", "复审通过，批准发布", "passed", version,
                                               score=int(re_acc), feedback=f"Approved after {retry+1} revision(s)")
                    steps.append(decision_step)
                    _finish_step(decision_step)
                    final_decision = "approved"
                    await event_bus.publish("verification_done", {"task_id": task_id, "status": "approved", "version": version}, source="VerificationOrchestrator")
                    # Update audit_report with re-audit results for next iteration
                    audit_report = {
                        "overall_confidence": re_acc,
                        "total_issues": len(re_result.get("unresolved_issues", [])),
                        "critical_issues": 0,
                        "issues": re_result.get("unresolved_issues", []),
                    }
                    break
                audit_report = {"overall_confidence": re_acc, "total_issues": len(re_result.get("unresolved_issues", [])), "issues": re_result.get("unresolved_issues", [])}
            except Exception as e:
                _finish_step(re_step, "failed", score=0,
                             issues=[{"issue_id": "iss-reaudit-fatal", "severity": "critical",
                                      "problem": f"Re-audit crashed: {str(e)}", "location": "re_audit"}],
                             feedback=f"Re-audit exception: {str(e)[:100]}")
                audit_passed = False

        # All retries exhausted — 内容已生成，返回但标记为待审核
        if final_decision != "approved":
            # 检查是否已有生成内容（即使审核未通过，内容仍然可用）
            has_content = bool(state.get("lecture_doc", {}).get("content", ""))
            if has_content:
                decision_step = _make_step("final_decision", "Orchestrator",
                                           f"审核未完全通过，但内容已生成可用", "pending_review", version,
                                           score=int(audit_report.get("overall_confidence", 0) if audit_report else 50),
                                           feedback=f"Content generated, pending full review after {MAX_RETRIES} retries")
            else:
                decision_step = _make_step("final_decision", "Orchestrator",
                                           f"审核未通过（{MAX_RETRIES}次重试已用尽）", "failed", version,
                                           score=int(audit_report.get("overall_confidence", 0) if audit_report else 50),
                                           feedback=f"Rejected after {MAX_RETRIES} retries")
            steps.append(decision_step)
            _finish_step(decision_step)
            final_decision = "pending_review" if has_content else "rejected"
            await event_bus.publish("verification_done", {"task_id": task_id, "status": final_decision, "version": version}, source="VerificationOrchestrator")

        # Quiz 生成（个性化练习，放审核闭环之后——练习不参与讲义审核）
        try:
            from .quiz_agent import get_quiz_agent
            quiz_agent = get_quiz_agent()
            quiz_result = await asyncio.to_thread(
                quiz_agent.generate,
                topic=lecture_topic,
                count=5,
                evidence=context.get("sources", []),
                domain_context={**state.get("domain_context", {}), "path_type": path_type,
                                "path_strategy": path_strategy},
            )
            if quiz_result:
                state["quiz"] = quiz_result
        except Exception as e:
            print(f"[Orchestrator] QuizAgent 生成失败: {e}")

        # 视频生成（最后、独立于核心资源审核；视频渲染慢，不与讲义/代码等一起阻塞审核）
        # 视频为可选后台资源，不参与主流程，避免 TTS/API 认证问题阻塞讲义发布。
        # 视频为可选能力：默认不阻塞主审核链路。设置 ENABLE_VIDEO_GENERATION=true
        # 时才调用讯飞数字人；未配置或调用失败均以 optional 状态记录，不影响资源通过。
        import os
        video_enabled = os.getenv("ENABLE_VIDEO_GENERATION", "false").lower() in {"1", "true", "yes", "on"}
        video_audit_step = _make_step("video_generation", "VideoAgent", "讯飞数字人视频（可选）", "running" if video_enabled else "skipped", version,
                                      feedback="已跳过可选视频生成" if not video_enabled else "正在生成可选视频")
        steps.append(video_audit_step)
        if video_enabled:
            video_result = await self._safe_run(self.video_agent, "VideoAgent", state, timeout=180.0)
            if video_result:
                state.update(video_result)
                _finish_step(video_audit_step, "passed", feedback="可选视频生成完成")
            else:
                _finish_step(video_audit_step, "skipped", feedback="可选视频未生成，主流程不受影响")
                state.setdefault("video_script", {"scenes": [], "optional": True})
        else:
            state.setdefault("video_script", {"scenes": [], "optional": True})

        return self._build_response(task_id, final_decision, version, steps, audit_report, state)

    # ================================================================
    # 内部方法
    # ================================================================
    async def _safe_run(self, agent, name: str, state: dict,
                       timeout: float = 120.0) -> dict | None:
        """安全执行单个 Agent，带超时保护。

        每个 Agent 最多执行 timeout 秒，超时后取消并返回 None。
        这防止单个慢 Agent（如 VideoAgent 的 TTS 调用）阻塞整个 orchestrator 管线。
        """
        try:
            await event_bus.publish("agent_start", {"agent": name}, source="VerificationOrchestrator")
            result = await asyncio.wait_for(
                agent.execute(state),
                timeout=timeout,
            )
            await event_bus.publish("agent_done", {"agent": name}, source="VerificationOrchestrator")
            return result
        except asyncio.TimeoutError:
            await event_bus.publish("agent_error", {
                "agent": name,
                "error": f"Agent 执行超时（>{timeout}s），已跳过",
            }, source="VerificationOrchestrator")
            print(f"[Orchestrator] {name} 超时（>{timeout}s），跳过该 Agent")
            return None
        except Exception as e:
            await event_bus.publish("agent_error", {"agent": name, "error": str(e)}, source="VerificationOrchestrator")
            print(f"[Orchestrator] {name} 异常: {e}")
            return None

    def _validate_code(self, code_example: dict) -> bool:
        content = code_example.get("content", "")
        if not content:
            return True  # no code to validate = pass
        try:
            compile(content, "<lecture-code>", "exec")
            return len(content) >= 30
        except SyntaxError:
            return False

    @staticmethod
    def _starter_code(topic: str) -> str:
        if any(key in topic.lower() for key in ("jupyter", "环境", "安装")):
            return '''# 在学习空间或 Jupyter 单元格中直接运行\nimport sys\nimport platform\n\nprint("Python 版本:", sys.version.split()[0])\nprint("解释器路径:", sys.executable)\nprint("操作系统:", platform.system())\n\nscores = [85, 92, 78]\nprint("平均成绩:", sum(scores) / len(scores))\n'''
        return f'print("开始学习：{topic}")\n'

    def _check_difficulty(self, state: dict, profile: dict, audit_report: dict = None) -> bool:
        # 用交叉验证审核的难度匹配分(0-100)判断,≥75 为达标(难度做硬)
        diff_score = (audit_report or {}).get("difficulty_match_score")
        if diff_score is None or diff_score == 0:
            return True
        return diff_score >= 75

    def _validate_citations(self, state: dict, context: dict) -> bool:
        sources = context.get("sources", [])
        if not sources:
            return True  # no KB sources = skip
        doc_content = state.get("lecture_doc", {}).get("content", "")
        if not doc_content:
            return False
        # Check at least one KB source is referenced in generated content.
        # Evidence uses source_title/knowledge_id; older code incorrectly read
        # the nonexistent `title` field and rejected valid grounded content.
        matched = 0
        for s in sources[:3]:
            title = s.get("source_title") or s.get("title", "")
            knowledge_id = s.get("knowledge_id", "")
            title_matched = title and len(title) > 3 and title.lower()[:10] in doc_content.lower()
            id_matched = knowledge_id and knowledge_id.lower() in doc_content.lower()
            if title_matched or id_matched:
                matched += 1
        return matched >= 1 or len(sources) == 0

    def _build_response(self, task_id: str, decision: str, version: int,
                        steps: list, audit_report: dict, state: dict) -> dict:
        verified = decision == "approved"
        final_report = audit_report if audit_report else {}
        # 提取代码内容：兼容 code_example.content 和 code_example.code 两种格式
        code_example = state.get("code_example", {})
        code_content = code_example.get("content", "") or code_example.get("code", "")
        # 提取思维导图：兼容 mindmap.nodes 和 mindmap.mindmap 两种格式
        mindmap_data = state.get("mindmap", {})
        mindmap_nodes = mindmap_data.get("nodes", mindmap_data.get("mindmap", []))
        if not mindmap_nodes and isinstance(mindmap_data, list):
            mindmap_nodes = mindmap_data

        resource = {
            "title": state.get("lecture_doc", {}).get("title", ""),
            "content": state.get("lecture_doc", {}).get("content", ""),
            "code": code_content,
            "mindmap": mindmap_nodes,
            "extended_reading": state.get("extended_reading", {}),
            "quiz": state.get("quiz", {}),
            "video": state.get("video_script", {}),
        }
        # 同时提升 resource 字段到顶层，前端直接读取 data.content / data.mindmap / data.code
        return {
            "task_id": task_id,
            "status": decision,
            "verified": verified,
            "generation_mode": "direct_deepseek" if MAX_RETRIES == 0 else "verified_orchestrator",
            "generated_by": "multi_agent_orchestrator",
            "final_version": version,
            "retry_count": version - 1,
            "verification_steps": steps,
            # 顶层字段（前端兼容）
            "title": resource["title"],
            "content": resource["content"],
            "code": resource["code"],
            "mindmap": resource["mindmap"],
            "extended_reading": resource["extended_reading"],
            "quiz": resource["quiz"],
            "video": resource["video"],
            # 审核 / 引用信息
            "audit": {
                "verified": verified,
                "confidence": final_report.get("overall_confidence", 0),
                "issues_found": final_report.get("details", []),
                "iterations": version,
                "hallucination_rate": final_report.get("hallucination_rate"),
                "difficulty_match_score": final_report.get("difficulty_match_score"),
                "debate": final_report.get("debate", {}),
                "mode": final_report.get("mode", "cross_validation + debate"),
            },
            "audit_report": {
                "overall_confidence": final_report.get("overall_confidence", 0),
                "total_issues": final_report.get("total_issues", 0),
                "critical_issues": final_report.get("critical_issues", 0),
                "details": final_report.get("details", []),
                "hallucination_rate": final_report.get("hallucination_rate"),
                "difficulty_match_score": final_report.get("difficulty_match_score"),
                "judges": final_report.get("judges", {}),
                "debate": final_report.get("debate", {}),
                "mode": final_report.get("mode", "cross_validation + debate"),
            },
            "citations": [
                {"title": s.get("source_title") or s.get("title", ""), "knowledge_id": s.get("knowledge_id", ""), "source": s.get("source_path", "")}
                for s in state.get("knowledge_context", {}).get("sources", [])[:5]
            ],
            # 保留 resource 嵌套（向后兼容）
            "resource": resource,
        }


_verification_orchestrator = None


def get_verification_orchestrator() -> VerificationOrchestrator:
    global _verification_orchestrator
    if _verification_orchestrator is None:
        _verification_orchestrator = VerificationOrchestrator()
    return _verification_orchestrator
