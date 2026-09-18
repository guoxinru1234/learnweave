#!/bin/bash
# ============================================================
# 阶段2: 克隆 OpenMAIC + DeepTutor
# ============================================================
source "$(dirname "$0")/common.sh"

PHASE="phase-2"

if is_phase_done "$PHASE"; then
    log_warn "阶段2已完成，跳过。"
    exit 0
fi

log_step "阶段2: 克隆开源项目"
check_git

REPOS_DIR="$ROOT/repos"
mkdir -p "$REPOS_DIR"

OPENMAIC_URL="https://github.com/THU-MAIC/OpenMAIC.git"
DEEPTUTOR_URL="https://github.com/HKUDS/DeepTutor.git"

# Clone OpenMAIC
if [ -d "$REPOS_DIR/OpenMAIC" ]; then
    log_info "OpenMAIC 已存在，拉取最新..."
    cd "$REPOS_DIR/OpenMAIC" && git pull --depth=1 2>/dev/null || true
else
    log_info "克隆 OpenMAIC (清华)..."
    git clone --depth=1 "$OPENMAIC_URL" "$REPOS_DIR/OpenMAIC" 2>&1 | tail -1
fi
log_ok "OpenMAIC: $(cd "$REPOS_DIR/OpenMAIC" && git log -1 --format='%h %s' 2>/dev/null || echo '就绪')"

# Clone DeepTutor
if [ -d "$REPOS_DIR/DeepTutor" ]; then
    log_info "DeepTutor 已存在，拉取最新..."
    cd "$REPOS_DIR/DeepTutor" && git pull --depth=1 2>/dev/null || true
else
    log_info "克隆 DeepTutor (港大)..."
    git clone --depth=1 "$DEEPTUTOR_URL" "$REPOS_DIR/DeepTutor" 2>&1 | tail -1
fi
log_ok "DeepTutor: $(cd "$REPOS_DIR/DeepTutor" && git log -1 --format='%h %s' 2>/dev/null || echo '就绪')"

# 分析代码结构
log_info "分析代码结构..."
echo ""
echo "OpenMAIC 关键目录:"
find "$REPOS_DIR/OpenMAIC" -maxdepth 2 -type d -not -path '*/.git/*' -not -path '*/node_modules/*' | head -15
echo ""
echo "DeepTutor 关键目录:"
find "$REPOS_DIR/DeepTutor" -maxdepth 2 -type d -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' | head -15

# 保存结构信息
mkdir -p "$ROOT/repos"
cat > "$ROOT/repos/structure.json" << 'STRUCTEOF'
{
  "openmaic": {
    "url": "https://github.com/THU-MAIC/OpenMAIC",
    "license": "AGPL-3.0",
    "stack": "Next.js + React + TypeScript + LangGraph",
    "purpose": "前端壳 + 多Agent课堂框架"
  },
  "deeptutor": {
    "url": "https://github.com/HKUDS/DeepTutor",
    "license": "Apache-2.0",
    "stack": "Python + Next.js",
    "purpose": "画像引擎(3层记忆) + RAG + 题库生成",
    "key_modules": ["profile_engine", "rag", "quiz_generator"]
  }
}
STRUCTEOF

mark_phase_done "$PHASE"
