#!/bin/bash
# ============================================================
# LearnMate 公共工具函数
# ============================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROGRESS_FILE="$ROOT/.progress"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo ""; echo -e "${GREEN}════════════════════════════════════════${NC}"; echo -e "${GREEN}  $*${NC}"; echo -e "${GREEN}════════════════════════════════════════${NC}"; echo ""; }

# 检查阶段是否已完成
is_phase_done() {
    local phase="$1"
    grep -q "^${phase}=done$" "$PROGRESS_FILE" 2>/dev/null
}

# 标记阶段完成
mark_phase_done() {
    local phase="$1"
    mkdir -p "$(dirname "$PROGRESS_FILE")"
    if ! grep -q "^${phase}=" "$PROGRESS_FILE" 2>/dev/null; then
        echo "${phase}=done" >> "$PROGRESS_FILE"
    else
        sed -i.bak "s/^${phase}=.*/${phase}=done/" "$PROGRESS_FILE"
    fi
    log_ok "阶段 ${phase} 标记完成"
}

# 检查 Python 依赖
check_python() {
    if ! command -v python3 &>/dev/null; then
        log_error "需要 Python 3.10+，请先安装"
        exit 1
    fi
    log_ok "Python $(python3 --version) 已就绪"
}

# 检查 Node 依赖
check_node() {
    if ! command -v node &>/dev/null; then
        log_error "需要 Node.js 18+，请先安装"
        exit 1
    fi
    log_ok "Node $(node --version) 已就绪"
}

# 检查 Git
check_git() {
    if ! command -v git &>/dev/null; then
        log_error "需要 Git，请先安装"
        exit 1
    fi
    log_ok "Git $(git --version | awk '{print $3}') 已就绪"
}
