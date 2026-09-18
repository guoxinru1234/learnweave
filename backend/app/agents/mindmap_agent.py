"""思维导图生成 Agent。

职责：将知识点组织为树形 JSON 结构，供前端渲染交互式思维导图。
根据学习模式自适应调整节点数量。
"""

import json
import re
from typing import Dict, Any

from .base import BaseAgent

MINDMAP_SYSTEM_PROMPT = """你是知识结构专家，擅长将课程内容组织为丰富、多层次的思维导图。

导图设计要求：
- 根节点 = 讲次主题
- 一级子节点 = 核心知识板块（6-8个）
- 二级子节点 = 具体知识点（每个板块3-5个）
- 三级子节点 = 关键细节/示例/注意事项（每个知识点1-3个）
- 至少3层深度，总共20-35个节点
- 覆盖：概念定义、核心原理、关键技术、实践应用、常见误区、优化技巧
- 层级关系逻辑清晰，节点标签具体有信息量
"""


class MindmapAgent(BaseAgent):
    """思维导图 Agent —— 生成树形 JSON 知识导图。"""

    def __init__(self):
        super().__init__("MindmapAgent", MINDMAP_SYSTEM_PROMPT)

    @staticmethod
    def _knowledge_only(data):
        """过滤习题/作业节点，导图仅保留知识点。"""
        blocked = re.compile(r"练习|习题|作业|测试|题目|答案|quiz|exercise|homework", re.I)
        def clean(node):
            if not isinstance(node, dict): return None
            label = str(node.get("label") or node.get("t") or "")
            if blocked.search(label): return None
            out = dict(node)
            if isinstance(out.get("children"), list):
                out["children"] = [x for x in (clean(c) for c in out["children"]) if x]
            return out
        if isinstance(data, dict) and isinstance(data.get("nodes"), list):
            return {**data, "nodes": [x for x in (clean(n) for n in data["nodes"]) if x]}
        if isinstance(data, list): return [x for x in (clean(n) for n in data) if x]
        return data

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state.get("lecture_topic", "")
        mode = state.get("mode", "study")
        context = state.get("knowledge_context", {})
        domain_context = state.get("domain_context", {})
        # 参考已生成的讲义（如果有的话）
        lecture_doc = state.get("lecture_doc", {})

        # 1. 优先 LLM 生成丰富多层导图（完整学习资源，每个节点带实质内容）
        parsed = None
        try:
            prompt = self._build_prompt(topic, mode, context, lecture_doc, domain_context)
            raw = await self._call_llm(prompt, temperature=0.4, max_tokens=3000)
            parsed = self._parse_json(raw)
        except Exception as e:
            self.log(f"LLM 生成失败: {e}")

        # 2. LLM 失败才从讲义 HTML 提取结构兜底（秒出，质量较低）
        if not parsed:
            lecture_html = lecture_doc.get("content", "")
            if lecture_html and len(lecture_html) > 100:
                parsed = self._extract_from_html(lecture_html, topic)

        # 3. 最终兜底
        if not parsed:
            parsed = self._fallback(topic)

        node_count = len(parsed.get("nodes", []))
        self.log(f"思维导图生成完成，{node_count} 个节点")
        return {"mindmap": self._knowledge_only(parsed)}


    def _extract_from_html(self, html: str, topic: str):
        import re
        # 按文档顺序提取 h3(章节)/strong(小节与概念，附带解释 note)/code(代码与术语)，
        # 构建 4 层树：章节 → 小节 → 概念(带一句解释) → 代码/术语。
        tag_re = re.compile(r'<(h3|strong|code)[^>]*>(.*?)</\1>', re.DOTALL)
        roots = []
        cur_ch = cur_sec = cur_con = None
        seen = set()
        for m in tag_re.finditer(html):
            tag = m.group(1)
            content = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if tag == 'h3':
                cur_ch = {'id': str(len(roots) + 1), 'label': content[:26], 'children': []}
                roots.append(cur_ch)
                cur_sec = cur_con = None
            elif tag == 'strong':
                if cur_ch is None or content in seen:
                    continue
                seen.add(content)
                label = content[:40]
                # 提取该概念后的正文作为一句解释（到下一个结构标签/段落结束为止）
                after = html[m.end():]
                nxt = re.search(r'</p>|<strong|<code|<h3|<p>', after)
                note = after[:nxt.start()] if nxt else after
                note = re.sub(r'<[^>]+>', '', note)
                note = re.sub(r'^[—–:：、,，.。\s]+', '', note).strip()[:40]
                if re.match(r'^\d+(\.\d+)', label) or re.match(r'^(案例|情况|错误|坑)\d*', label):
                    cur_sec = {'id': label, 'label': label, 'children': []}
                    cur_ch['children'].append(cur_sec)
                    cur_con = None
                else:
                    node = {'id': label, 'label': label, 'children': []}
                    if note:
                        node['note'] = note
                    (cur_sec['children'] if cur_sec is not None else cur_ch['children']).append(node)
                    cur_con = node
            elif tag == 'code':
                t = content
                if 2 <= len(t) <= 28:
                    target = cur_con if cur_con is not None else cur_sec
                    if target is not None and t not in [c['label'] for c in target['children']]:
                        target['children'].append({'id': t, 'label': t})

        if len(roots) < 2:
            return None
        return {"nodes": [{"id": "1", "label": topic, "children": roots}]}

    def _build_prompt(self, topic: str, mode: str, context: dict,
                      lecture_doc: dict, domain_context: dict = None) -> str:
        mode_config = self._get_mode_config(mode)
        node_range = mode_config.get("mindmap_nodes", "8-10")
        domain_context = domain_context or {}
        level = domain_context.get("level", "intermediate")
        depth_hint = {
            "basic": "以梳理基础概念为主，节点标签带简短解释，适合零基础入门",
            "intermediate": "覆盖概念+核心API+常见坑，兼顾理论与实践",
            "advanced": "深入底层原理、性能优化、进阶技巧，适合有基础的学习者",
        }.get(level, "覆盖概念+核心API+常见坑")

        # 知识库上下文
        context_text = ""
        if context:
            original_mindmap = context.get("mindmap", [])
            if original_mindmap:
                context_text = f"【知识库中已有的导图节点】：{json.dumps(original_mindmap, ensure_ascii=False)}\n请基于这些节点进行重组和扩展。"
            else:
                content_raw = context.get("content", "")
                plain = re.sub(r'<[^>]+>', '', content_raw)[:500]
                context_text = f"【知识库内容摘要】：{plain}\n请根据此摘要生成思维导图。"

        # 已生成的讲义内容（如果 DocAgent 已在并行中完成）
        lecture_hint = ""
        if lecture_doc.get("content"):
            html = lecture_doc["content"]
            # 提取章节标题作为导图一级分支的结构来源，保证导图与讲义大纲同步
            headings = re.findall(r'<(?:h2|h3)[^>]*>(.*?)</(?:h2|h3)>', html, re.DOTALL)
            headings = [re.sub(r'<[^>]+>', '', h).strip()[:30]
                        for h in headings if re.sub(r'<[^>]+>', '', h).strip()]
            plain_content = re.sub(r'<[^>]+>', '', html)[:1500]
            if headings:
                lecture_hint = (
                    "\n【已生成的讲义章节大纲】（导图的一级分支务必与这些章节一一对应）：\n"
                    + "、".join(headings)
                    + f"\n【讲义内容摘要】：{plain_content}\n请严格基于这份讲义的大纲与内容生成导图节点。"
                )
            else:
                lecture_hint = f"\n【已生成的讲义内容摘要】：{plain_content}\n请基于此讲义摘要生成导图节点。"

        return f"""请将以下知识点组织为一棵详尽的思维导图树，以 JSON 格式输出。

【知识点】：{topic}
【模式】：{mode_config['label']}
【个性化侧重】：{depth_hint}
【要求】：总共50-80个节点，至少4层深度，覆盖全部子知识点。每个节点标签控制在15字以内，精炼表达。
{context_text}{lecture_hint}

输出格式（严格 JSON）：
{{
  "nodes": [
    {{"id": "1", "label": "根节点标题", "children": [
      {{"id": "1-1", "label": "一级分支(具体概念名)", "children": [
        {{"id": "1-1-1", "label": "二级：核心API/方法名"}},
        {{"id": "1-1-2", "label": "二级：关键参数"}},
        {{"id": "1-1-3", "label": "二级：返回值类型"}},
        {{"id": "1-1-4", "label": "二级：代码示例(一行)"}}
      ]}},
      {{"id": "1-2", "label": "一级分支2", "children": [
        {{"id": "1-2-1", "label": "二级知识点"}},
        {{"id": "1-2-2", "label": "二级知识点", "children": [
          {{"id": "1-2-2-1", "label": "三级：具体细节/注意事项"}},
          {{"id": "1-2-2-2", "label": "三级：常见错误"}}
        ]}}
      ]}}
    ]}}
  ]
}}

硬性要求（不满足会重试）：
- 至少8个一级分支，用具体概念名（如"广播机制"而非"工作原理"）
- 每个一级分支至少3个二级子节点，标签要带简短解释（如"iloc[行号,列号]：按整数位置选取数据"而非只写"iloc"）
- 关键节点扩展到三级，叶子节点写一句解释（如"axis=0沿行计算→每列一个结果"）
- 代码示例节点写完整一行代码（如"df.loc[df.age>30, ['name','age']]"）
- 注意事项节点说明原因（如"切片是视图不是副本→修改会影响原数组"）
- 基于知识库和讲义内容生成，确保准确性
- 总节点数不少于50个

只输出 JSON，不要其他文字。"""

    def _parse_json(self, raw: str) -> dict | None:
        """从 LLM 回复中解析 JSON，多种策略尝试。"""
        import re as _re
        # 策略1: ```json ... ```
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError):
            pass
        # 策略2: 尝试提取 {...} 或 [ 开始的JSON
        for pattern in [_re.compile(r'\{[\s\S]*"nodes"[\s\S]*\}'), _re.compile(r'\[[\s\S]*\{[\s\S]*\}[\s\S]*\]')]:
            m = pattern.search(raw)
            if m:
                try: return json.loads(m.group())
                except: pass
        return None

    def _fallback(self, topic: str) -> dict:
        """基于讲次主题关键词生成针对性的兜底导图，不再是泛词模板。"""
        tl = topic.lower()
        if any(k in tl for k in ['jupyter','环境','python环境','搭建','安装','配置']):
            children = [
{"id":"1-1","label":"环境选择","children":[{"id":"1-1-1","label":"Anaconda(自带250+库)"},{"id":"1-1-2","label":"Miniconda(轻量版)"},{"id":"1-1-3","label":"pip+venv(纯Python)"},{"id":"1-1-4","label":"Python版本选3.10+"}]},{"id":"1-2","label":"安装步骤","children":[{"id":"1-2-1","label":"Win:下载安装包→勾选PATH"},{"id":"1-2-2","label":"Mac:brew install python"},{"id":"1-2-3","label":"验证:python --version"},{"id":"1-2-4","label":"conda --version验证"}]},{"id":"1-3","label":"Jupyter操作","children":[{"id":"1-3-1","label":"启动:jupyter notebook"},{"id":"1-3-2","label":"Cell类型:Code/Markdown/Raw"},{"id":"1-3-3","label":"运行:Shift+Enter"},{"id":"1-3-4","label":"新建:b下方/a上方"},{"id":"1-3-5","label":"删除:dd连按两次d"}]},{"id":"1-4","label":"核心库安装","children":[{"id":"1-4-1","label":"numpy:数值计算基础"},{"id":"1-4-2","label":"pandas:数据处理核心"},{"id":"1-4-3","label":"matplotlib:绑图库"},{"id":"1-4-4","label":"seaborn:统计可视化"},{"id":"1-4-5","label":"scikit-learn:机器学习"}]},{"id":"1-5","label":"常见问题","children":[{"id":"1-5-1","label":"python命令不存在→检查PATH"},{"id":"1-5-2","label":"pip安装慢→换清华镜像源"},{"id":"1-5-3","label":"Jupyter连不上→--no-browser"},{"id":"1-5-4","label":"Anaconda与旧Python冲突→卸载一个"}]},{"id":"1-6","label":"虚拟环境管理","children":[{"id":"1-6-1","label":"venv:python -m venv myenv"},{"id":"1-6-2","label":"激活:myenv/Scripts/activate"},{"id":"1-6-3","label":"conda create -n myenv python=3.10"}]},{"id":"1-7","label":"IDE选择","children":[{"id":"1-7-1","label":"VS Code+Python插件"},{"id":"1-7-2","label":"PyCharm Community"},{"id":"1-7-3","label":"JupyterLab(升级版)"}]},{"id":"1-8","label":"依赖管理","children":[{"id":"1-8-1","label":"pip freeze > requirements.txt"},{"id":"1-8-2","label":"pip install -r requirements.txt"},{"id":"1-8-3","label":"conda env export > env.yml"}]},
            ]
        elif any(k in tl for k in ['变量','数据类型','运算符','类型']):
            children = [
                {"id":"1-1","label":"变量与赋值","children":[{"id":"1-1-1","label":"动态类型(vs静态)"},{"id":"1-1-2","label":"命名规则(PEP8)"},{"id":"1-1-3","label":"多重赋值a,b=1,2"}]},
                {"id":"1-2","label":"基本类型","children":[{"id":"1-2-1","label":"int/float/bool"},{"id":"1-2-2","label":"str字符串操作"},{"id":"1-2-3","label":"类型转换int()/str()"}]},
                {"id":"1-3","label":"容器类型","children":[{"id":"1-3-1","label":"list可变有序"},{"id":"1-3-2","label":"tuple不可变"},{"id":"1-3-3","label":"dict键值映射"},{"id":"1-3-4","label":"set去重集合"}]},
                {"id":"1-4","label":"运算符","children":[{"id":"1-4-1","label":"算术+ - * / // % **"},{"id":"1-4-2","label":"比较== != > <"},{"id":"1-4-3","label":"逻辑and or not"}]},
                {"id":"1-5","label":"常见坑","children":[{"id":"1-5-1","label":"5/2=2.5不是2"},{"id":"1-5-2","label":"得分+str(95)类型错误"},{"id":"1-5-3","label":"可变默认参数陷阱"}]},
                {"id":"1-6","label":"实战技巧","children":[{"id":"1-6-1","label":"f-string格式化"},{"id":"1-6-2","label":"split/join字符串"},{"id":"1-6-3","label":"isinstance类型检查"}]},
            ]
        elif any(k in tl for k in ['numpy','数组','array','矩阵','ndarray']):
            children = [
                {"id":"1-1","label":"数组创建","children":[{"id":"1-1-1","label":"np.array()/zeros()/ones()"},{"id":"1-1-2","label":"np.arange()/linspace()"},{"id":"1-1-3","label":"np.random随机数组"}]},
                {"id":"1-2","label":"数组属性","children":[{"id":"1-2-1","label":"shape/ndim/dtype/size"},{"id":"1-2-2","label":"reshape变形"},{"id":"1-2-3","label":"astype类型转换"}]},
                {"id":"1-3","label":"索引切片","children":[{"id":"1-3-1","label":"整数索引arr[0]"},{"id":"1-3-2","label":"切片arr[1:4]"},{"id":"1-3-3","label":"布尔索引arr[arr>5]"},{"id":"1-3-4","label":"花式索引arr[[0,2]]"}]},
                {"id":"1-4","label":"运算与广播","children":[{"id":"1-4-1","label":"向量化运算arr*2"},{"id":"1-4-2","label":"通用函数np.sqrt/sin"},{"id":"1-4-3","label":"广播机制(不同shape运算)"}]},
                {"id":"1-5","label":"统计函数","children":[{"id":"1-5-1","label":"sum/mean/std/var"},{"id":"1-5-2","label":"axis=0列=1行"},{"id":"1-5-3","label":"percentile百分位数"}]},
                {"id":"1-6","label":"视图vs副本","children":[{"id":"1-6-1","label":"切片是视图(共享数据)"},{"id":"1-6-2","label":".copy()创建副本"},{"id":"1-6-3","label":"何时必须用copy"}]},
            ]
        elif any(k in tl for k in ['pandas','dataframe','series','表格']):
            children = [
                {"id":"1-1","label":"数据结构","children":[{"id":"1-1-1","label":"Series一维标签数组"},{"id":"1-1-2","label":"DataFrame二维表格"},{"id":"1-1-3","label":"Index索引对象"}]},
                {"id":"1-2","label":"数据读写","children":[{"id":"1-2-1","label":"pd.read_csv/excel/json"},{"id":"1-2-2","label":"df.to_csv保存"},{"id":"1-2-3","label":"encoding编码处理"}]},
                {"id":"1-3","label":"数据查看","children":[{"id":"1-3-1","label":"head/tail/info/describe"},{"id":"1-3-2","label":"shape/dtypes/columns"},{"id":"1-3-3","label":"value_counts统计"}]},
                {"id":"1-4","label":"索引筛选","children":[{"id":"1-4-1","label":"loc标签iloc位置"},{"id":"1-4-2","label":"布尔筛选df[df.age>30]"},{"id":"1-4-3","label":"query/isin方法"}]},
                {"id":"1-5","label":"分组聚合","children":[{"id":"1-5-1","label":"groupby分组"},{"id":"1-5-2","label":"agg多函数聚合"},{"id":"1-5-3","label":"pivot_table透视表"}]},
                {"id":"1-6","label":"数据清洗","children":[{"id":"1-6-1","label":"dropna/fillna缺失值"},{"id":"1-6-2","label":"drop_duplicates去重"},{"id":"1-6-3","label":"astype类型转换"}]},
            ]
        else:
            children = [
                {"id":"1-1","label":"核心概念","children":[{"id":"1-1-1","label":"定义与原理"}]},
                {"id":"1-2","label":"关键方法/API","children":[{"id":"1-2-1","label":"常用函数"}]},
                {"id":"1-3","label":"代码示例","children":[{"id":"1-3-1","label":"基础用法"}]},
                {"id":"1-4","label":"常见场景","children":[{"id":"1-4-1","label":"实战案例"}]},
                {"id":"1-5","label":"注意点","children":[{"id":"1-5-1","label":"易错/性能考虑"}]},
                {"id":"1-6","label":"进阶延伸","children":[{"id":"1-6-1","label":"关联知识点"}]},
            ]
        return {"nodes": [{"id": "1", "label": topic, "children": children}]}
