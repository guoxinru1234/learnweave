# backend/app/agents/course_agent.py
"""课程生成智能体（deprecated: 推荐使用 UnifiedOrchestrator 的多 Agent 协作模式）

此文件保留用于向后兼容。新代码请通过 UnifiedOrchestrator 分别调用
DocAgent, MindmapAgent, CodeAgent, QuizAgent 生成各自资源。
"""
import json
from ..core.llm import get_llm_client


class CourseAgent:
    """课程生成智能体：自动生成完整讲义

    @deprecated: generate_lecture_structured() 一次 LLM 调用产出所有资源，
    不符合比赛"多智能体协同"要求。推荐使用 UnifiedOrchestrator。
    """

    def __init__(self):
        print("[INFO] CourseAgent 初始化 (统一 LLMClient)...")
        self.llm = get_llm_client()

    def _call_llm(self, prompt: str, max_tokens: int = 4000) -> str:
        """同步调用 LLM（底层 LLMClient 自带 3 次重试）"""
        messages = [{"role": "user", "content": prompt}]
        return self.llm.chat_sync(messages, temperature=0.7, max_tokens=max_tokens)

    def generate_lecture(self, course_title: str, lecture_topic: str, knowledge_base: str = "") -> dict:
        prompt = f"""
你是一位资深的大数据技术讲师。请为以下课程生成一份完整、详细的讲义。

课程：{course_title}
讲次：{lecture_topic}
{f'参考知识库：{knowledge_base}' if knowledge_base else ''}

讲义要求：
1. 内容要详细、有深度，让学生能完整理解整个章节
2. 每个部分要有充分的解释和说明
3. 重点突出，难点剖析透彻
4. 适合制作成 60-90 秒的教学视频

请按照以下格式输出 JSON：
{{
    "title": "讲次标题",
    "duration": "建议时长（分钟）",
    "learning_objectives": ["学习目标1", "学习目标2", "学习目标3", "学习目标4"],
    "content": {{
        "introduction": "引言（80-120字），包括背景、为什么重要、与实际应用的关联",
        "core_knowledge": {{
            "concept": "核心概念详细解释（150-200字），包括定义、特征、关键要素",
            "principles": "原理详细说明（150-200字），包括工作机制、关键流程、核心思想",
            "steps": ["详细步骤1", "详细步骤2", "详细步骤3", "详细步骤4"],
            "example": "应用示例说明（60-80字）"
        }},
        "key_points": [
            "重点1：详细说明（30-50字）",
            "重点2：详细说明（30-50字）",
            "重点3：详细说明（30-50字）"
        ],
        "confusion_points": {{
            "point": "易混淆点描述（20-30字）",
            "comparison": "详细对比说明（60-80字），包括正确理解和常见误解的对比",
            "takeaway": "关键区别总结（20-30字）"
        }},
        "summary": "总结（60-80字），强调核心要点和实际应用价值",
        "practice": ["练习题1（具体描述）", "练习题2（具体描述）", "练习题3（具体描述）"]
    }}
}}
"""
        try:
            content = self._call_llm(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"API 调用失败，使用备选方案: {e}")
            return self.generate_lecture_fallback(course_title, lecture_topic)

    def generate_lecture_fallback(self, course_title: str, lecture_topic: str) -> dict:
        """备选方案：生成详细、完整的讲义（内容丰富，适合教学）"""
        # 这里你可以保留你自己之前写的完整硬编码内容
        # 目前提供一个最小示例以便运行
        return {
            "title": lecture_topic,
            "duration": "10分钟",
            "learning_objectives": [f"理解 {lecture_topic}", f"掌握 {lecture_topic}"],
            "content": {
                "introduction": f"{lecture_topic} 是重要概念。",
                "core_knowledge": {
                    "concept": f"{lecture_topic} 的概念",
                    "principles": f"{lecture_topic} 的原理",
                    "steps": ["步骤1", "步骤2"],
                    "example": "示例"
                },
                "key_points": [f"{lecture_topic} 重点1", f"{lecture_topic} 重点2"],
                "confusion_points": {
                    "point": "易混淆点",
                    "comparison": "对比",
                    "takeaway": "关键区别"
                },
                "summary": f"{lecture_topic} 总结",
                "practice": ["练习题1", "练习题2"]
            }
        }

    def generate_lecture_structured(self, course_title: str, lecture_topic: str, lecture_num: int) -> dict:
        prompt = f"""
你是一位资深的大数据技术教授，擅长把复杂的技术概念讲得清晰易懂。

请为以下课程生成一份**完整、详尽**的讲次内容，让学生学完这一讲后能够完全掌握该知识点，**不需要去其他地方查阅资料**。

课程：{course_title}
讲次：{lecture_topic}

请按照以下结构组织内容：

1. 【引言】（100-150字）
   - 为什么这个知识点重要？
   - 在实际工作中哪里会用到？
   - 与其他知识点的关联

2. 【核心概念】（150-200字）
   - 用通俗易懂的语言解释核心概念
   - 给出明确的定义和关键特征

3. 【工作原理】（150-200字）
   - 详细说明工作机制和流程
   - 可以分步骤描述

4. 【关键流程/步骤】（100-150字）
   - 具体的操作步骤或处理流程
   - 配上代码示例

5. 【重点总结】（3-5个点）
   - 必须掌握的核心知识点
   - 每个点用 30-50 字说明

6. 【易混淆点对比】（1-2个）
   - 哪些概念容易混淆？
   - 用对比的方式说明区别

7. 【完整代码示例】（可直接运行）
   - 一个完整的、可运行的代码示例
   - 包含必要的注释

8. 【总结】（80-100字）
   - 回顾本讲核心内容
   - 给出下一步学习建议

总字数要求：800-1500字，确保内容足够全面。

请输出 JSON 格式：
{{
    "title": "{lecture_topic}",
    "type": "理论课",
    "content": "HTML 格式的完整讲义，用 <h3>、<p>、<ul>、<li>、<strong>、<code> 等标签组织。重点用 [Star]重点 标记，易混淆点用 [WARN]易混淆 标记。",
    "code": "完整可运行的 Python 数据分析代码示例",
    "mindmap": [
        {{"t": "知识点1", "s": "简短说明"}},
        {{"t": "知识点2", "s": "简短说明"}},
        {{"t": "知识点3", "s": "简短说明"}},
        {{"t": "知识点4", "s": "简短说明"}},
        {{"t": "知识点5", "s": "简短说明"}}
    ],
    "quiz": {{
        "question": "单选题题目（围绕核心知识点）",
        "options": [
            {{"text": "正确选项（包含正确解释）", "correct": true}},
            {{"text": "干扰项1（常见错误理解）", "correct": false}},
            {{"text": "干扰项2", "correct": false}},
            {{"text": "干扰项3", "correct": false}}
        ]
    }}
}}
"""
        try:
            content = self._call_llm(prompt)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            print(f"生成讲义失败: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_structured(lecture_topic)

    def _generate_fallback_structured(self, lecture_topic: str) -> dict:
        return {
            "title": lecture_topic,
            "type": "理论课",
            "content": f"""
<h3>📌 课程说明</h3>
<p>本节将系统讲解 <strong>{lecture_topic}</strong> 的核心知识和实践应用。</p>

<h3>[Target] 学习目标</h3>
<ul>
  <li>理解 {lecture_topic} 的基本概念和定义</li>
  <li>掌握 {lecture_topic} 的核心原理和工作机制</li>
  <li>了解 {lecture_topic} 在实际项目中的应用场景</li>
  <li>能够独立完成 {lecture_topic} 相关的代码实现</li>
</ul>

<h3>📖 内容概览</h3>
<p>本讲内容由 AI 智能体自动生成。请配置有效的 API Key 后，系统将自动生成包含详细概念解释、原理说明、代码示例、易混淆点对比和练习题的完整讲义。</p>

<h3>[Idea] 学习建议</h3>
<ul>
  <li>先通读讲义，建立整体认知</li>
  <li>重点关注核心概念和关键流程</li>
  <li>动手运行代码示例，加深理解</li>
  <li>完成课后练习题，巩固知识</li>
</ul>
""",
            "code": f"""// {lecture_topic} 代码示例
// 请配置 API Key 后获取详细内容

object LectureExample {{
  def main(args: Array[String]): Unit = {{
    println("正在学习: {lecture_topic}")
  }}
}}""",
            "mindmap": [
                {"t": f"{lecture_topic} 概述", "s": "核心概念"},
                {"t": f"{lecture_topic} 原理", "s": "工作机制"},
                {"t": f"{lecture_topic} 实现", "s": "代码实践"},
                {"t": "常见问题", "s": "注意事项"},
                {"t": "扩展应用", "s": "进阶方向"},
            ],
            "quiz": {
                "question": f"{lecture_topic} 的核心思想是什么？",
                "options": [
                    {"text": "正确理解：核心是高效处理数据", "correct": True},
                    {"text": "错误理解1：只关注表面概念", "correct": False},
                    {"text": "错误理解2：不需要理解原理", "correct": False},
                    {"text": "错误理解3：只背诵定义即可", "correct": False},
                ]
            }
        }