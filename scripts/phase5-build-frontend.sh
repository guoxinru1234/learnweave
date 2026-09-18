#!/bin/bash
# ============================================================
# 阶段5: 构建 Next.js 前端
# ============================================================
source "$(dirname "$0")/common.sh"

PHASE="phase-5"

if is_phase_done "$PHASE"; then
    log_warn "阶段5已完成，跳过。"
    exit 0
fi

log_step "阶段5: 构建前端"

check_node

FRONTEND_DIR="$ROOT/frontend"
OPENMAIC_REPO="$ROOT/repos/OpenMAIC"

# 如果 OpenMAIC 有可用代码，基于它创建
if [ -d "$OPENMAIC_REPO" ] && [ -f "$OPENMAIC_REPO/package.json" ]; then
    log_info "基于 OpenMAIC 创建前端..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        # OpenMAIC 使用 pnpm workspace
        if ! command -v pnpm &>/dev/null; then
            npm install -g pnpm --quiet 2>/dev/null || true
        fi
        cp -r "$OPENMAIC_REPO"/* "$FRONTEND_DIR/" 2>/dev/null || true
        cd "$FRONTEND_DIR" && pnpm install --no-frozen-lockfile 2>&1 | tail -5
    fi
else
    log_info "OpenMAIC 未就绪，从 Next.js 模板创建..."
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --no-turbopack --use-npm 2>&1 | tail -5 || true
    fi
fi

# 安装额外依赖
cd "$FRONTEND_DIR" 2>/dev/null && pnpm add lucide-react recharts framer-motion 2>&1 | tail -2 || true

# 生成设计规范参考文档
cat > "$FRONTEND_DIR/DESIGN_SPEC.md" << 'DOCEOF'
# LearnMate 设计规范

参考: ui-prototype/index.html (v6, 3721行生产级原型)

## 色彩系统
- Primary: #4F46E5 (Indigo)
- Success: #16A34A (Green)
- Warning: #D97706 (Amber)
- Danger: #DC2626 (Red)
- Background: #EEF2FF (Light) / #0F0E1A (Dark)

## 字体
- 正文: Fira Sans
- 代码: Fira Code

## 图标
- Lucide React (lucide-react)
- 禁止使用 emoji 作为结构图标

## 组件规范
- 圆角: 12-24px (Bento Grid 风格)
- 阴影: 四层系统 (sm/md/lg/xl)
- 卡片: 白色底 + hover 上浮 2px
- 按钮: 主色填充 / 次色描边 / ghost 透明

## 页面列表
1. Dashboard — Bento Grid + 多Agent工作流
2. Profile — 6维雷达图 + 对话式构建
3. Learning Space — 5 Tab 多模态
4. Quiz — 知识点分类 + 错题重练
5. Tutor — 流式打字 AI 对话
6. Assessment — Bullet Chart + 动态建议
DOCEOF

log_ok "前端项目已初始化"
mark_phase_done "$PHASE"
