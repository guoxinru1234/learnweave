from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
import os
import json
import uuid
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.llm import get_llm_client

router = APIRouter(prefix="/api/agent", tags=["agent"])

# ==================== 请求/响应模型 ====================
class AgentRequest(BaseModel):
    prompt: str
    mode: Optional[str] = "study"  # preview | study | review | challenge
    profile: Optional[Dict[str, Any]] = None  # 学生画像
    course_id: Optional[str] = None  # 课程ID，用于加载知识库
    lecture_num: Optional[int] = None  # 讲次编号，用于加载知识库

class AgentResponse(BaseModel):
    success: bool
    output: str
    steps: list = []
    mode: str = "study"
    recommendation: Optional[str] = None  # 推荐模式说明

# ==================== 模式配置 ====================
MODE_CONFIG = {
    "preview": {
        "label": "[Look] 预习模式",
        "description": "快速浏览核心概念，适合课前预习",
        "depth": "浅",
        "examples": 1,
        "code_complexity": "简单",
        "quiz_count": 2,
        "mindmap_nodes": "4-6",
        "prompt_suffix": """
【学习模式】：预习模式
- 只输出核心概念（不超过3个）
- 只给1个简单例子
- 不深入原理细节
- 代码只需展示核心语法，不加复杂逻辑
- 练习题只出2道基础题
"""
    },
    "study": {
        "label": "📖 学习模式",
        "description": "系统学习完整内容，适合正常学习",
        "depth": "中",
        "examples": 2,
        "code_complexity": "标准",
        "quiz_count": 4,
        "mindmap_nodes": "8-10",
        "prompt_suffix": """
【学习模式】：学习模式
- 输出完整内容：概念 + 原理 + 2个案例 + 总结
- 原理讲解清晰，有逐步推导
- 代码完整，有详细注释
- 练习题4道（2道基础 + 2道中等）
"""
    },
    "review": {
        "label": "[Memo] 复习模式",
        "description": "快速回顾重点，适合考前复习",
        "depth": "浅",
        "examples": 1,
        "code_complexity": "标准",
        "quiz_count": 6,
        "mindmap_nodes": "10-12",
        "prompt_suffix": """
【学习模式】：复习模式
- 只输出重点总结和易混淆点对比
- 不需要完整原理讲解，只需要关键结论
- 1个综合案例（整合多个知识点）
- 练习题6道（中等难度，覆盖所有重点）
"""
    },
    "challenge": {
        "label": "[Win] 挑战模式",
        "description": "深度钻研 + 综合应用，适合进阶学习",
        "depth": "深",
        "examples": 3,
        "code_complexity": "复杂",
        "quiz_count": 4,
        "mindmap_nodes": "12-15",
        "prompt_suffix": """
【学习模式】：挑战模式
- 深度原理讲解（包括底层实现、性能分析）
- 3个渐进式案例（基础→进阶→综合）
- 代码包含优化技巧和最佳实践
- 练习题4道（2道中等 + 2道困难）
- 附加拓展阅读建议
"""
    }
}

# ==================== 知识库工具：从缓存加载讲义 ====================
def load_lecture_from_cache(course_id: str, lecture_num: int) -> Dict[str, Any]:
    """
    从本地 lecture_cache 加载讲次内容，作为知识库上下文（防幻觉）
    """
    cache_dir = Path("data/lecture_cache")
    cache_file = cache_dir / f"{course_id}_{lecture_num}.json"

    if not cache_file.exists():
        print(f"[WARN]️ 缓存文件不存在: {cache_file}")
        return {}

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"[OK] 从缓存加载知识库: {course_id}_{lecture_num}")
            return data
    except Exception as e:
        print(f"[X] 读取缓存失败: {e}")
        return {}

# ==================== 回调处理器 ====================
class AgentStepTracker(BaseCallbackHandler):
    def __init__(self):
        self.steps = []
        self.current_tool = None

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        tool_name = serialized.get("name", "unknown")
        self.current_tool = {
            "id": str(len(self.steps) + 1),
            "name": tool_name,
            "status": "running",
            "description": f"正在执行 {tool_name}",
            "input": input_str[:50] + ("..." if len(input_str) > 50 else ""),
        }
        self.steps.append(self.current_tool)

    def on_tool_end(self, output: Any, **kwargs) -> None:
        if self.current_tool:
            try:
                output_preview = "执行完成"
                if output is None:
                    output_preview = "无输出"
                elif hasattr(output, "content") and output.content is not None:
                    output_preview = str(output.content)[:100]
                elif isinstance(output, str):
                    output_preview = output[:100]
                elif isinstance(output, dict):
                    output_preview = json.dumps(output, ensure_ascii=False)[:100]
                else:
                    output_preview = str(output)[:100]
            except Exception:
                output_preview = "（无法获取输出预览）"

            self.current_tool["status"] = "success"
            self.current_tool["description"] = f"{self.current_tool['name']} 执行完成"
            self.current_tool["output_preview"] = output_preview + ("..." if len(str(output)) > 100 else "")
            self.current_tool = None

    def on_tool_error(self, error: Exception, **kwargs) -> None:
        if self.current_tool:
            self.current_tool["status"] = "error"
            self.current_tool["description"] = f"{self.current_tool['name']} 执行失败: {str(error)[:50]}"
            self.current_tool = None

    def on_agent_action(self, action: AgentAction, **kwargs) -> None:
        pass

    def on_agent_finish(self, finish: AgentFinish, **kwargs) -> None:
        pass


# ==================== 工具函数：模式推荐 ====================
def recommend_mode(profile: Dict[str, Any]) -> Dict[str, Any]:
    foundation = profile.get("foundation", "中等")
    goal = profile.get("goal", "")
    weakness = profile.get("weakness", [])

    if foundation in ["零基础", "入门"]:
        return {"mode": "preview", "reason": "你的基础需要从核心概念开始"}
    if weakness and any(kw in goal for kw in ["考试", "证书", "复习", "通过"]):
        return {"mode": "review", "reason": f"你有 {len(weakness)} 个薄弱点，建议复习巩固"}
    if foundation in ["良好", "精通"] and len(weakness) >= 2:
        return {"mode": "challenge", "reason": "你的基础较好，推荐深度挑战"}
    if foundation in ["中等", "良好"]:
        return {"mode": "study", "reason": "适合系统学习完整内容"}
    return {"mode": "study", "reason": "推荐标准学习模式"}


# ==================== 1. 画像构建 Agent ====================
def profile_agent(input: str) -> str:
    llm = get_llm_client()
    prompt = f"""你是一位专业的学情画像分析专家。请从以下用户描述中抽取 6 个维度的学情画像信息，并以 JSON 格式输出。

用户描述：
{input}

必须包含字段：
1. major: 专业（如：计算机科学与技术）
2. grade: 年级（如：大二）
3. foundation: 知识基础（零基础/入门/中等/良好/精通）
4. style: 学习风格（视觉型/听觉型/动手型/理论型/综合型）
5. goal: 学习目标（具体描述）
6. weakness: 薄弱点（数组，如 ["Shuffle", "内存管理"]）

只返回 JSON，不要其他文字。"""
    try:
        raw = llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        data = json.loads(raw)
        for f in ["major", "grade", "foundation", "style", "goal", "weakness"]:
            if f not in data:
                data[f] = "未知" if f != "weakness" else []
        return json.dumps(data, ensure_ascii=False)
    except:
        return json.dumps({
            "major": "计算机科学与技术",
            "grade": "大二",
            "foundation": "中等",
            "style": "综合型",
            "goal": "掌握 Python 数据分析",
            "weakness": ["Shuffle", "内存管理"]
        }, ensure_ascii=False)


# ==================== 2. 文档生成 Agent（基于知识库 + 模式） ====================
def doc_agent(topic: str, profile: Dict[str, Any], mode: str, context: Dict[str, Any]) -> str:
    llm = get_llm_client()

    mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])
    foundation = profile.get("foundation", "中等")
    style = profile.get("style", "综合型")
    weakness = profile.get("weakness", [])

    style_hint = {
        "视觉型": "多用图表、流程图、代码高亮来呈现",
        "听觉型": "语言要清晰、有节奏感，多用类比",
        "动手型": "多给可运行的代码示例和练习",
        "理论型": "深入原理，给出严谨的推导过程",
        "综合型": "平衡理论与实践的呈现"
    }.get(style, "平衡理论与实践的呈现")

    weakness_hint = ""
    if weakness:
        weakness_hint = f"\n注意：学生的薄弱点包括 {', '.join(weakness)}，在文档中需要重点讲解这些内容，用更多案例和解释帮助理解。"

    # 构建知识库上下文（防幻觉核心）
    context_text = ""
    if context:
        # 取标题和内容
        title = context.get("title", topic)
        content_raw = context.get("content", "")
        # 清洗 HTML 标签以获取纯文本（简单处理）
        import re
        plain_text = re.sub(r'<[^>]+>', '', content_raw)
        context_text = f"""
【知识库参考内容（来自权威讲义）】：
标题：{title}
内容摘要：{plain_text[:1500]}

请严格基于以上参考内容（而非你的记忆）进行总结、重组和扩写，确保生成的内容绝对准确，杜绝幻觉。
"""
    else:
        context_text = "【注意】：没有找到对应的知识库内容，请基于你的专业知识生成准确内容。"

    prompt = f"""你是一位资深课程讲师。请根据以下要求生成一份 Markdown 格式的学习讲义。

{context_text}

【主题】：{topic}

【学生画像】：
- 专业：{profile.get('major', '未知')}
- 年级：{profile.get('grade', '未知')}
- 知识基础：{foundation}
- 学习风格：{style} → 呈现方式：{style_hint}
{weakness_hint}

{mode_config['prompt_suffix']}

【额外要求】：
- 内容深度：{mode_config['depth']}
- 案例数量：{mode_config['examples']} 个
- 语言风格：根据学生的 {foundation} 基础调整难度

只返回 Markdown 内容，不要其他文字。"""

    try:
        return llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
    except Exception as e:
        print(f"[X] doc_agent 生成失败: {e}")
        # 降级方案：如果 LLM 生成失败，直接返回缓存原文（确保讲义不空）
        if context and context.get("content"):
            return f"# {topic}\n\n（基于知识库内容）\n\n{context.get('content')}"
        return f"# {topic}\n\n## 概念\n（生成失败，请稍后重试: {str(e)}）"


# ==================== 3. 题库生成 Agent ====================
def quiz_agent(topic: str, profile: Dict[str, Any], mode: str) -> str:
    llm = get_llm_client()
    mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])
    foundation = profile.get("foundation", "中等")
    weakness = profile.get("weakness", [])

    difficulty_map = {
        "零基础": "简单，考察基本概念",
        "入门": "简单到中等，考察概念和理解",
        "中等": "中等，考察理解和应用",
        "良好": "中等偏难，考察应用和分析",
        "精通": "困难，考察分析、综合和评价"
    }
    difficulty = difficulty_map.get(foundation, "中等")

    weakness_hint = ""
    if weakness and mode in ["review", "challenge"]:
        weakness_hint = f"\n重点考察薄弱点：{', '.join(weakness)}，至少出 1 道相关题目。"

    prompt = f"""请根据以下知识点生成 {mode_config['quiz_count']} 道练习题，以 JSON 格式返回。

【知识点】：{topic}
【题目难度】：{difficulty}
【题目数量】：{mode_config['quiz_count']} 道
【模式】：{mode_config['label']}
{weakness_hint}

格式要求：
{{
  "quiz": [
    {{"type": "choice", "question": "题目", "options": ["A", "B", "C", "D"], "answer": "A", "difficulty": "简单/中等/困难"}},
    {{"type": "fill", "question": "填空题题目（用 _____ 表示填空）", "answer": "正确答案", "difficulty": "简单/中等/困难"}}
  ]
}}

要求：
- 选择题和填空题混合，至少包含 1 道选择题
- 在预习模式下：只出简单题
- 在复习模式下：出中等题为主
- 在挑战模式下：出中等和困难题混合

只返回 JSON，不要其他文字。"""
    try:
        raw = llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
        )
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return raw
    except:
        return json.dumps({
            "quiz": [
                {"type": "choice", "question": "示例题目", "options": ["A", "B", "C", "D"], "answer": "A", "difficulty": "中等"}
            ]
        })


# ==================== 4. 思维导图 Agent（基于知识库 + 模式） ====================
def mindmap_agent(topic: str, profile: Dict[str, Any], mode: str, context: Dict[str, Any]) -> str:
    llm = get_llm_client()
    mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])

    # 构建知识库上下文（防止思维导图内容跑偏）
    context_text = ""
    if context:
        # 提取思维导图原始数据（如果有）
        original_mindmap = context.get("mindmap", [])
        if original_mindmap:
            context_text = f"【知识库中的思维导图节点】：{json.dumps(original_mindmap, ensure_ascii=False)}\n请基于这些节点进行重组。"
        else:
            # 如果没有现成导图，使用内容
            content_raw = context.get("content", "")
            import re
            plain_text = re.sub(r'<[^>]+>', '', content_raw)[:500]
            context_text = f"【知识库内容摘要】：{plain_text}\n请根据此摘要生成思维导图。"

    prompt = f"""请将以下知识点组织为树形思维导图，以 JSON 格式输出。

【知识点】：{topic}
【模式】：{mode_config['label']}
【要求节点数】：{mode_config['mindmap_nodes']} 个

{context_text}

格式：
{{
  "nodes": [
    {{"id": "1", "label": "根节点", "children": [{{"id": "2", "label": "子节点"}}]}}
  ]
}}

要求：
- 预习模式：只包含核心概念，节点数 4-6 个
- 学习模式：完整知识结构，节点数 8-10 个
- 复习模式：突出重点和关联，节点数 10-12 个
- 挑战模式：包含拓展和进阶内容，节点数 12-15 个

只返回 JSON，不要其他文字。"""
    try:
        raw = llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800,
        )
        # raw already contains the content from chat_sync
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return raw
    except:
        return json.dumps({
            "nodes": [{"id": "1", "label": topic, "children": [{"id": "2", "label": "待补充"}]}]
        })


# ==================== 5. 代码生成 Agent ====================
def code_agent(topic: str, profile: Dict[str, Any], mode: str) -> str:
    llm = get_llm_client()
    mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])
    foundation = profile.get("foundation", "中等")
    code_complexity = mode_config['code_complexity']
    if foundation in ["零基础", "入门"]:
        code_complexity = "简单"

    prompt = f"""请根据以下需求生成一段可运行的 Python 代码，并附上注释。

【主题】：{topic}
【代码复杂度】：{code_complexity}
【模式】：{mode_config['label']}

要求：
- 预习模式：只有 3-5 行核心语法，无复杂逻辑
- 学习模式：完整可运行代码，详细注释
- 复习模式：整合多个知识点的综合代码
- 挑战模式：包含性能优化、高级特性的代码

只返回代码块（用 ```scala ... ``` 包裹），不要其他文字。"""
    try:
        raw = llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        return raw
    except:
        return "// 生成失败，请重试"


# ==================== 6. 路径规划 Agent ====================
def path_agent(topic: str, profile: Dict[str, Any], mode: str) -> str:
    llm = get_llm_client()
    mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])
    foundation = profile.get("foundation", "中等")
    step_count = 3 if mode == "preview" else 5 if mode == "study" else 6 if mode == "review" else 8

    prompt = f"""请根据以下学情画像和学习模式，规划一条个性化的学习路径，以 JSON 格式输出。

【画像】：
- 专业：{profile.get('major', '未知')}
- 年级：{profile.get('grade', '未知')}
- 知识基础：{foundation}
- 薄弱点：{profile.get('weakness', [])}
- 学习目标：{profile.get('goal', '无')}

【学习模式】：{mode_config['label']}
【路径步数】：{step_count} 步

输出格式：
{{
  "steps": ["第1步：...", "第2步：...", ...],
  "resources": ["推荐资源1", "推荐资源2", ...],
  "estimated_time": "预计学习时间",
  "focus_areas": ["重点领域1", "重点领域2"]
}}

要求：
- 预习模式：快速路径，3-4 步，突出核心概念
- 学习模式：完整路径，5-6 步，覆盖所有知识点
- 复习模式：精简路径，4-5 步，聚焦重点和薄弱点
- 挑战模式：深度路径，7-8 步，包含进阶内容

只返回 JSON。"""
    try:
        raw = llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800,
        )
        # raw already contains the content from chat_sync
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return raw
    except:
        return json.dumps({
            "steps": ["第1步：基础概念", "第2步：核心原理", "第3步：实战应用"],
            "resources": ["官方文档", "视频教程", "练习题库"],
            "estimated_time": "3周",
            "focus_areas": ["核心概念", "应用实践"]
        })


# ==================== FastAPI 路由 ====================
@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """LangChain Agent 调度器（向后兼容）。

    @deprecated: 推荐使用 /api/lecture/{course_id}/{lecture_num}/multi-agent
    该端点使用 UnifiedOrchestrator（LangGraph 多 Agent 并行编排）。
    本端点保留用于向后兼容。
    """
    try:
        # 1. 获取画像
        profile = request.profile or {}
        if not profile:
            profile = {
                "major": "计算机科学与技术",
                "grade": "大二",
                "foundation": "中等",
                "style": "综合型",
                "goal": "掌握 Python 数据分析",
                "weakness": ["Shuffle", "内存管理"]
            }

        # 2. 获取模式
        mode = request.mode or "study"
        recommendation = None
        if not request.mode:
            rec = recommend_mode(profile)
            mode = rec["mode"]
            recommendation = rec["reason"]

        mode_config = MODE_CONFIG.get(mode, MODE_CONFIG["study"])

        # 3. [Fire] 加载知识库上下文（从缓存加载讲义）
        context = {}
        if request.course_id and request.lecture_num:
            print(f"[Book] 尝试加载知识库: {request.course_id}_{request.lecture_num}")
            context = load_lecture_from_cache(request.course_id, request.lecture_num)
        else:
            print("[WARN]️ 未提供 course_id/lecture_num，将不使用知识库")

        # 4. 包装工具函数（传入画像、模式和上下文）
        def profile_wrapper(input: str) -> str:
            return profile_agent(input)

        def doc_wrapper(input: str) -> str:
            return doc_agent(input, profile, mode, context)

        def quiz_wrapper(input: str) -> str:
            return quiz_agent(input, profile, mode)

        def mindmap_wrapper(input: str) -> str:
            return mindmap_agent(input, profile, mode, context)

        def code_wrapper(input: str) -> str:
            return code_agent(input, profile, mode)

        def path_wrapper(input: str) -> str:
            return path_agent(input, profile, mode)

        # 5. 初始化模型
        model = ChatOpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            temperature=0.7,
        )

        # 6. 定义工具
        tools = [
            StructuredTool.from_function(
                func=profile_wrapper,
                name="profile_agent",
                description="构建学生画像（6 维度）"
            ),
            StructuredTool.from_function(
                func=doc_wrapper,
                name="doc_agent",
                description="生成 Markdown 讲解文档"
            ),
            StructuredTool.from_function(
                func=quiz_wrapper,
                name="quiz_agent",
                description="生成练习题"
            ),
            StructuredTool.from_function(
                func=mindmap_wrapper,
                name="mindmap_agent",
                description="生成思维导图"
            ),
            StructuredTool.from_function(
                func=code_wrapper,
                name="code_agent",
                description="生成代码示例"
            ),
            StructuredTool.from_function(
                func=path_wrapper,
                name="path_agent",
                description="规划学习路径"
            ),
        ]

        # 7. 系统 Prompt
        system_prompt = f"""你是 LearnWeave 多智能体系统的调度器。

当前学习模式：{mode_config['label']}
模式说明：{mode_config['description']}

学生画像：
- 专业：{profile.get('major', '未知')}
- 知识基础：{profile.get('foundation', '中等')}
- 薄弱点：{', '.join(profile.get('weakness', []))}
- 学习风格：{profile.get('style', '综合型')}

根据以上画像和模式，选择合适的工具生成个性化学习资源。
{'' if not recommendation else f'系统推荐：{recommendation}'}
"""

        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt
        )

        user_message = f"{request.prompt}\n\n当前模式：{mode_config['label']}，请根据画像生成对应资源。"

        tracker = AgentStepTracker()
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config={"callbacks": [tracker]}
        )

        # 8. 提取输出
        output = "未提取到答案"
        if "messages" in result:
            for msg in reversed(result["messages"]):
                if hasattr(msg, "role") and msg.role == "assistant" and hasattr(msg, "content") and msg.content:
                    output = msg.content
                    break
                elif isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
                    output = msg["content"]
                    break
        else:
            if hasattr(result, "output"):
                output = result.output
            elif isinstance(result, dict) and "output" in result:
                output = result["output"]

        # 9. 构建 steps
        if tracker.steps:
            steps = tracker.steps
        else:
            steps = [
                {"id": "1", "name": "[Robot] 调度器", "status": "success", "description": f"模式：{mode_config['label']}"}
            ]

        for step in steps:
            if "id" not in step:
                step["id"] = str(uuid.uuid4())[:8]
            if "status" not in step:
                step["status"] = "success"
            if "description" not in step:
                step["description"] = step.get("name", "任务完成")

        if not steps:
            steps = [{"id": "1", "name": "处理完成", "status": "success", "description": "任务已完成"}]

        return AgentResponse(
            success=True,
            output=output,
            steps=steps,
            mode=mode,
            recommendation=recommendation
        )

    except Exception as e:
        print("[X] Agent 执行失败:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))