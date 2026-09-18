#!/bin/bash
# ============================================================
# 阶段6: Ralph 自主迭代开发 + 质量把关
# 前提: 阶段1-5已完成
# 用法: make ralph [MAX_ITERATIONS=10]
# ============================================================
source "$(dirname "$0")/common.sh"

PHASE="phase-6"
MAX_ITERATIONS="${1:-10}"

if is_phase_done "$PHASE"; then
    log_warn "阶段6已完成，跳过。（删除 .progress 强制重跑）"
    exit 0
fi

log_step "阶段6: Ralph 自主迭代开发"

# 前置检查
check_git
check_python
check_node

RALPH_SCRIPT="$ROOT/scripts/ralph/ralph.sh"
PRD_FILE="$ROOT/config/prd.json"

if [ ! -f "$RALPH_SCRIPT" ]; then
    log_error "Ralph 脚本未找到: $RALPH_SCRIPT"
    exit 1
fi

chmod +x "$RALPH_SCRIPT"

# 确保测试框架就绪
log_info "验证后端测试框架..."
cd "$ROOT/backend"
if [ ! -f "pytest.ini" ] && [ ! -f "pyproject.toml" ]; then
    cat > pytest.ini << 'PYEOF'
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
PYEOF
    mkdir -p tests
    cat > tests/test_health.py << 'PYEOF'
"""基础健康检查测试"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_backend_structure():
    """验证后端目录结构"""
    app_dir = os.path.join(os.path.dirname(__file__), '..', 'app')
    assert os.path.exists(app_dir), "app 目录缺失"
    assert os.path.exists(os.path.join(app_dir, 'main.py')), "main.py 缺失"

def test_knowledge_base():
    """验证知识库存在"""
    kb_path = os.path.join(os.path.dirname(__file__), '..', '..', 'knowledge-base', 'index.json')
    assert os.path.exists(kb_path), "知识库 index.json 缺失"

def test_rag_module():
    """验证RAG模块可导入"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from app.rag.engine import RAGEngine
    assert RAGEngine is not None
PYEOF
    log_ok "后端测试框架已初始化"
fi

log_info "验证前端测试框架..."
cd "$ROOT/frontend" 2>/dev/null
if [ -f "package.json" ] && ! grep -q '"test"' package.json 2>/dev/null; then
    npm install --save-dev vitest @testing-library/react @testing-library/jest-dom 2>&1 | tail -1 || true
    log_ok "前端测试框架已初始化"
fi

# 生成 PRD（如果不存在）
if [ ! -f "$PRD_FILE" ]; then
    log_info "生成 PRD (从竞赛要求 + 设计规范)..."
    python3 "$ROOT/scripts/generate-prd.py" "$PRD_FILE" 2>/dev/null || {
        log_info "PRD生成脚本未就绪，使用模板..."
        cp "$ROOT/scripts/ralph/prd.json.example" "$PRD_FILE"
    }
fi

# 验证 PRD
if ! python3 -c "import json; json.load(open('$PRD_FILE'))" 2>/dev/null; then
    log_error "PRD 格式无效: $PRD_FILE"
    exit 1
fi

STORY_COUNT=$(python3 -c "import json; d=json.load(open('$PRD_FILE')); print(len(d.get('stories',[])))")
log_info "PRD 包含 ${STORY_COUNT} 个用户故事"

# 确保 git 仓库就绪
cd "$ROOT"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init
    git add -A
    git commit -m "初始骨架: 5阶段构建完成" 2>/dev/null || true
    log_ok "Git 仓库已初始化"
fi

# 运行 Ralph
echo ""
log_info "启动 Ralph — 最大迭代: ${MAX_ITERATIONS} 次"
log_info "工具: Claude Code"
log_info "质量门禁: typecheck + pytest + vitest"
echo ""

cd "$ROOT"
bash "$RALPH_SCRIPT" --tool claude "$MAX_ITERATIONS"

# 检查结果
PASSED=$(python3 -c "import json; d=json.load(open('$PRD_FILE')); print(sum(1 for s in d.get('stories',[]) if s.get('passes')))")
TOTAL=$(python3 -c "import json; d=json.load(open('$PRD_FILE')); print(len(d.get('stories',[])))")

log_ok "Ralph 执行完成: ${PASSED}/${TOTAL} 故事通过"

if [ "$PASSED" -eq "$TOTAL" ]; then
    log_ok "所有故事通过质量检查!"
    mark_phase_done "$PHASE"
else
    log_warn "部分故事未通过，检查 config/prd.json 和 progress.txt"
fi
