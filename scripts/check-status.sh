#!/bin/bash
# ============================================================
# 查看项目构建状态
# ============================================================
source "$(dirname "$0")/common.sh" 2>/dev/null || true

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROGRESS_FILE="$ROOT/.progress"

echo ""
echo "  LearnMate 构建状态"
echo "  ══════════════════"
echo ""

check_phase() {
    local num="$1"
    local name="$2"
    local check_path="$3"
    local status="⬜ 未开始"
    
    if [ -f "$PROGRESS_FILE" ] && grep -q "^phase-${num}=done$" "$PROGRESS_FILE" 2>/dev/null; then
        status="✅ 完成"
    elif [ -d "$check_path" ] || [ -f "$check_path" ]; then
        status="🔄 进行中"
    fi
    printf "  %-8s %s\n" "阶段${num}:" "${name} — ${status}"
}

check_phase 1 "知识库提取"          "$ROOT/knowledge-base/index.json"
check_phase 2 "克隆开源项目"        "$ROOT/repos/OpenMAIC"
check_phase 3 "后端微服务"          "$ROOT/backend/app/main.py"
check_phase 4 "LangGraph多Agent"    "$ROOT/backend/app/agents/orchestrator.py"
check_phase 5 "Next.js前端"         "$ROOT/frontend/package.json"
check_phase 6 "AI自主迭代开发"      "$ROOT/scripts/ralph/ralph.sh"

echo ""
echo "  文件统计:"
echo "  ─────────"
KB_COUNT=$(find "$ROOT/knowledge-base" -path "$ROOT/knowledge-base/[0-9][0-9]/lecture.md" 2>/dev/null | wc -l | tr -d ' ')
BACKEND_COUNT=$(find "$ROOT/backend/app" "$ROOT/backend/tests" -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
FRONTEND_COUNT=$(find "$ROOT/frontend/app" "$ROOT/frontend/components" "$ROOT/frontend/lib" "$ROOT/frontend/tests" "$ROOT/frontend/e2e" \
    \( -path '*/node_modules/*' -o -path '*/.next/*' \) -prune -o \
    -type f \( -name '*.ts' -o -name '*.tsx' \) -print 2>/dev/null | wc -l | tr -d ' ')
EXPERIMENT_COUNT=$(find "$ROOT/../实验手册" -type f \
    ! -name '.DS_Store' 2>/dev/null | wc -l | tr -d ' ')
echo "  知识库: ${KB_COUNT} 个讲义 Markdown 文件"
echo "  实验手册: ${EXPERIMENT_COUNT} 个资料/数据文件"
echo "  后端代码: ${BACKEND_COUNT} 个 Python 文件 (app + tests)"
echo "  前端代码: ${FRONTEND_COUNT} 个 TypeScript/TSX 文件 (app/components/lib/tests/e2e)"
echo ""

if [ -f "$PROGRESS_FILE" ]; then
    DONE_COUNT=$(grep -c "=done$" "$PROGRESS_FILE" 2>/dev/null || echo 0)
    TOTAL_COUNT=6
    if [ "$DONE_COUNT" -gt "$TOTAL_COUNT" ]; then
        DONE_COUNT="$TOTAL_COUNT"
    fi
    echo "  总进度: ${DONE_COUNT}/${TOTAL_COUNT} 阶段完成"
else
    echo "  总进度: 0/6 阶段完成 (运行 'make all' 开始)"
fi
echo ""
