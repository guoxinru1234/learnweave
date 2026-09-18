"""Resource generation agent backed by course asset retrieval."""
from __future__ import annotations

import os
import json
import hashlib

from ..core.config import settings
from ..core.llm import get_llm_client
from ..rag.engine import RAGEngine


class ResourceAgent:
    """Generate learning resources from retrieved course assets.

    代码生成用 LLM，其他资源类型（summary/mindmap/practice）用确定性方法。
    """

    def __init__(self):
        print("[INFO] ResourceAgent 初始化 (统一 LLMClient)...")
        self.llm = get_llm_client()
        self.rag = RAGEngine(str(settings.kb_path))

        # 内存缓存（用于同一实例的多次调用，但实例是每次请求新建，所以主要靠文件缓存）
        self._cache = {}

    # ---------- 文件缓存方法 ----------
    def _get_cache_dir(self) -> str:
        """获取缓存目录路径，并确保存在"""
        cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'cache', 'resources')
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _get_cache_path(self, topic: str) -> str:
        """根据 topic 生成缓存文件路径（使用 MD5 避免文件名非法）"""
        safe_name = hashlib.md5(topic.encode('utf-8')).hexdigest()
        return os.path.join(self._get_cache_dir(), f"{safe_name}.json")

    def _load_from_cache(self, topic: str) -> dict | None:
        """从文件缓存加载数据"""
        path = self._get_cache_path(topic)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[OK] 从缓存文件加载 {topic} 的资源")
                    return data
            except Exception as e:
                print(f"[WARN] 缓存文件读取失败: {e}")
        return None

    def _save_to_cache(self, topic: str, data: dict) -> None:
        """保存数据到文件缓存"""
        path = self._get_cache_path(topic)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[OK] 已保存 {topic} 的资源到缓存文件: {path}")
        except Exception as e:
            print(f"[WARN] 缓存文件保存失败: {e}")

    # ---------- 主生成方法 ----------
    def generate(self, topic: str, resource_types: list[str] | None = None) -> dict:
        # 1. 尝试从文件缓存加载
        cached = self._load_from_cache(topic)
        if cached:
            return cached

        # 2. 内存缓存（如果实例复用）
        if topic in self._cache:
            print(f"[OK] 从内存缓存返回 {topic} 的资源")
            return self._cache[topic]

        # 3. 生成新内容
        resource_types = resource_types or ["summary", "mindmap", "code", "lab_hint", "practice"]
        sources = self.rag.search(topic, top_k=5)
        resources = []
        if "summary" in resource_types:
            resources.append(self._summary(topic, sources))
        if "mindmap" in resource_types:
            resources.append(self._mindmap(topic, sources))
        if "code" in resource_types:
            resources.append(self._code(topic, sources))
        if "lab_hint" in resource_types:
            resources.append(self._lab_hint(topic, sources))
        if "practice" in resource_types:
            resources.append(self._practice(topic, sources))

        result = {"topic": topic, "resources": resources, "sources": sources}

        # 4. 存入缓存
        self._cache[topic] = result
        self._save_to_cache(topic, result)
        print(f"[OK] 已缓存 {topic} 的资源（内存+文件）")
        return result

    # ---------- 以下方法保持不变（_summary, _mindmap, _code, ...） ----------
    # ... 请保留您现有的所有其他方法，包括 _summary, _mindmap, _code, _clean_code, _fallback_code, _lab_hint, _practice 等

    def _summary(self, topic: str, sources: list[dict]) -> dict:
        bullets = [
            f"围绕「{topic}」优先学习 {source['title']}。"
            for source in sources[:3]
        ] or [f"围绕「{topic}」建立概念、代码和实验三类材料。"]
        return {
            "type": "summary",
            "title": f"{topic} 学习摘要",
            "content": bullets,
        }

    def _mindmap(self, topic: str, sources: list[dict]) -> dict:
        children = []
        for source in sources[:4]:
            children.append({
                "label": source["title"],
                "type": source["category"],
                "topics": source.get("topics", []),
            })
        return {
            "type": "mindmap",
            "title": f"{topic} 知识导图",
            "root": topic,
            "children": children,
        }

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 并返回纯文本响应（底层 LLMClient 自带 3 次重试）"""
        return self.llm.chat_sync(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )

    def _code(self, topic: str, sources: list[dict]) -> dict:
        """使用 LLM 生成贴合主题的完整代码示例"""
        # 构建 RAG 上下文
        context_parts = []
        for src in sources[:3]:
            title = src.get("title", "")
            content = src.get("content", "") or src.get("text", "")
            if title:
                context_parts.append(f"《{title}》{content[:300]}")
        context = "\n".join(context_parts) if context_parts else "无额外参考资料"

        prompt = f"""
你是一位资深Python数据分析工程师，正在为课程「{topic}」编写教学代码示例。

**任务**：根据当前讲次主题「{topic}」，生成一段能充分体现该讲核心内容的 Python 数据分析代码。

**具体要求**：
- 代码必须与该讲次的主题**强相关**，不要使用与主题无关的通用示例。
- 如果主题涉及 NumPy，请重点演示数组操作、广播、向量化计算。
- 如果主题涉及 Pandas，请重点演示 DataFrame/Series 操作、数据筛选、分组聚合。
- 如果主题涉及数据清洗，请重点演示缺失值处理、类型转换、去重。
- 如果主题涉及数据可视化，请重点演示 Matplotlib/Seaborn 图表绘制。

**通用要求**：
- 代码语言：Python 3（包含 import 语句）。
- 添加详细的中文注释，逐行解释关键操作。
- 代码长度 20~40 行。
- 可直接在 Jupyter Notebook 或本地 Python 环境运行。

**参考课程资料**（供参考，不要直接复制）：
{context}

现在请输出**纯代码**，不要有任何额外解释或 Markdown 标记。
"""

        try:
            code = self._call_llm(prompt)
            code = self._clean_code(code)
            print(f"[OK] 代码生成成功，长度 {len(code)} 字符")
        except Exception as e:
            code = self._fallback_code(topic)
            print(f"[ResourceAgent] LLM 调用全部失败，使用降级模板。错误：{e}")

        return {
            "type": "code",
            "title": f"{topic} 示例代码",
            "language": "scala",
            "content": code,
        }

    def _clean_code(self, code: str) -> str:
        """去除 AI 可能添加的 markdown 代码块标记"""
        if code.startswith("```") and code.endswith("```"):
            lines = code.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()

    def _fallback_code(self, topic: str) -> str:
        """原有硬编码模板（作为 LLM 不可用时的备用）"""
        lower = topic.lower()
        if "dataframe" in lower or "sql" in lower:
            return "val df = spark.read.option(\"header\", \"true\").csv(\"data/score.csv\")\ndf.createOrReplaceTempView(\"score\")\nspark.sql(\"select * from score limit 5\").show()"
        elif "rdd" in lower or "shuffle" in lower:
            return "val rdd = sc.textFile(\"data/input.txt\")\nval counts = rdd.flatMap(_.split(\" \")).map((_, 1)).reduceByKey(_ + _)\ncounts.collect().foreach(println)"
        elif "yarn" in lower:
            return "spark-submit --class WordCount --master yarn --deploy-mode client target/app.jar"
        else:
            return "import pandas as pd\nimport numpy as np\n\n# 创建示例 DataFrame\ndf = pd.DataFrame({'A': [1,2,3], 'B': [4,5,6]})\nprint(df.describe())"

    def _lab_hint(self, topic: str, sources: list[dict]) -> dict:
        lab = next((source for source in sources if source["category"] in {"lab", "case"}), None)
        if not lab:
            return {
                "type": "lab_hint",
                "title": f"{topic} 实验建议",
                "content": "先完成对应讲义，再进行代码运行和结果截图记录。",
            }
        return {
            "type": "lab_hint",
            "title": f"推荐实验：{lab['title']}",
            "content": f"参考 {lab['source_path']}，先复现实验步骤，再记录关键命令、运行结果和错误排查过程。",
        }

    def _practice(self, topic: str, sources: list[dict]) -> dict:
        source_title = sources[0]["title"] if sources else topic
        return {
            "type": "practice",
            "title": f"{topic} 检查点",
            "content": [
                f"说明 {source_title} 的核心目标。",
                "列出运行该实验前必须检查的环境项。",
                "写出一个你认为最容易出错的步骤及排查方式。",
            ],
        }