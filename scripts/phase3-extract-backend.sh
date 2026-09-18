#!/bin/bash
# ============================================================
# 阶段3: 提取 DeepTutor 核心 → Python 微服务
# ============================================================
source "$(dirname "$0")/common.sh"

PHASE="phase-3"

if is_phase_done "$PHASE"; then
    log_warn "阶段3已完成，跳过。"
    exit 0
fi

log_step "阶段3: 构建后端微服务"

check_python

BACKEND_DIR="$ROOT/backend"
DEEPTUTOR_REPO="$ROOT/repos/DeepTutor"

# 创建 Python 虚拟环境
if [ ! -d "$BACKEND_DIR/venv" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv "$BACKEND_DIR/venv"
fi
source "$BACKEND_DIR/venv/bin/activate"

# 安装依赖
log_info "安装后端依赖..."
pip install --quiet fastapi uvicorn langchain langgraph openai chromadb pydantic python-multipart 2>/dev/null

# 如果 DeepTutor 存在，复制其核心模块
if [ -d "$DEEPTUTOR_REPO" ]; then
    log_info "从 DeepTutor 提取核心模块..."
    # 查找并复制 RAG 相关代码
    find "$DEEPTUTOR_REPO" -name "*.py" -path "*/rag*" -o -name "*.py" -path "*/retriev*" 2>/dev/null | head -5
    # 查找画像相关代码
    find "$DEEPTUTOR_REPO" -name "*.py" -path "*/profile*" -o -name "*.py" -path "*/memory*" 2>/dev/null | head -5
    log_info "DeepTutor 代码结构已分析，待后续集成"
fi

# 生成 FastAPI 主入口
cat > "$BACKEND_DIR/app/main.py" << 'PYEOF'
"""LearnMate Backend — FastAPI 微服务入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LearnMate API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "LearnMate Backend"}

@app.get("/api/knowledge/lectures")
async def list_lectures():
    """列出所有讲座"""
    import json, os
    kb_path = os.path.join(os.path.dirname(__file__), "../../knowledge-base/index.json")
    if os.path.exists(kb_path):
        with open(kb_path) as f:
            return json.load(f)
    return {"error": "知识库未初始化，请先运行 phase-1"}

@app.get("/api/knowledge/lecture/{lecture_id}")
async def get_lecture(lecture_id: str):
    """获取单个讲座内容"""
    import os
    md_path = os.path.join(os.path.dirname(__file__), f"../../knowledge-base/{lecture_id}/lecture.md")
    if os.path.exists(md_path):
        with open(md_path) as f:
            return {"content": f.read(), "id": lecture_id}
    return {"error": "讲座不存在"}
PYEOF

# 生成 RAG 模块骨架
cat > "$BACKEND_DIR/app/rag/__init__.py" << 'PYEOF'
"""RAG 检索增强生成模块"""
PYEOF

cat > "$BACKEND_DIR/app/rag/engine.py" << 'PYEOF'
"""RAG 检索引擎 (待从 DeepTutor 集成)"""
from typing import List
import os, json

class RAGEngine:
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.documents = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        index_path = os.path.join(self.kb_path, "index.json")
        if os.path.exists(index_path):
            with open(index_path) as f:
                self.index = json.load(f)

    def search(self, query: str, top_k: int = 3) -> List[dict]:
        """搜索相关知识 (关键字匹配，后续升级为向量检索)"""
        results = []
        if not hasattr(self, 'index'):
            return results
        for lec in self.index.get("lectures", []):
            if query.lower() in lec["title"].lower():
                results.append(lec)
        return results[:top_k]

    def get_context(self, query: str) -> str:
        """获取查询相关的知识上下文"""
        results = self.search(query)
        if not results:
            return ""
        contexts = []
        for r in results:
            md_path = os.path.join(self.kb_path, r["dir"], "lecture.md")
            if os.path.exists(md_path):
                with open(md_path) as f:
                    contexts.append(f.read()[:2000])
        return "\n\n".join(contexts)
PYEOF

# 生成画像模块骨架
cat > "$BACKEND_DIR/app/models/__init__.py" << 'PYEOF'
"""数据模型"""
PYEOF

cat > "$BACKEND_DIR/app/models/profile.py" << 'PYEOF'
"""学习者画像模型 (6维)"""
from pydantic import BaseModel
from typing import List, Optional

class LearnerProfile(BaseModel):
    knowledge_base: int = 72      # 知识基础
    cognitive_style: int = 80     # 认知风格
    weak_points: int = 55         # 易错规避
    learning_pace: int = 75       # 学习节奏
    modality_pref: int = 90       # 模态偏好
    motivation: int = 85          # 学习动机

    summaries: List[str] = [
        "已掌握 Java、操作系统、Linux 基础",
        "实践驱动型 — 偏好先动手编码再回溯理论",
        "Shuffle 机制（58%）· 流处理窗口（65%）",
        "每周约 6 小时 · 单次 45-60 分钟",
        "代码实操 > 图解动画 > 结构化文档",
        "目标明确（大数据工程师方向）"
    ]

    def to_array(self) -> List[int]:
        return [self.knowledge_base, self.cognitive_style, self.weak_points,
                self.learning_pace, self.modality_pref, self.motivation]
PYEOF

# 生成 requirements.txt
cat > "$BACKEND_DIR/requirements.txt" << 'PYEOF'
fastapi>=0.100.0
uvicorn>=0.23.0
langchain>=0.1.0
langgraph>=0.0.20
openai>=1.0.0
chromadb>=0.4.0
pydantic>=2.0.0
python-multipart>=0.0.6
python-docx>=0.8.11
PYEOF

log_ok "后端微服务骨架已生成"
mark_phase_done "$PHASE"
