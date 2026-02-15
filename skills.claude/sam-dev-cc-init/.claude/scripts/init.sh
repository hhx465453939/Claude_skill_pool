#!/bin/bash
# Sam Dev CC Init - PDCA 工作流初始化脚本
# 用法：./init.sh [项目名称]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目名称
PROJECT_NAME="${1:-$(basename "$PWD")}"
DATE=$(date +%Y-%m-%d)
SKILL_DIR="$HOME/.config/agents/skills/sam-dev-cc-init"

# 计数器
CREATED=0
SKIPPED=0

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}        🚀 PDCA 开发工作流初始化                          ${BLUE}║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "项目：${GREEN}$PROJECT_NAME${NC}"
    echo -e "日期：${GREEN}$DATE${NC}"
    echo ""
}

copy_template() {
    local src="$1"
    local dst="$2"
    local desc="$3"
    
    if [ -f "$dst" ]; then
        echo -e "  ${YELLOW}⏭${NC}  $desc (已存在，跳过)"
        ((SKIPPED++))
        return 0
    fi
    
    if [ -f "$src" ]; then
        sed -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" \
            -e "s/{{DATE}}/$DATE/g" \
            "$src" > "$dst"
        echo -e "  ${GREEN}✓${NC}  $desc"
        ((CREATED++))
    else
        echo -e "  ${RED}✗${NC}  $desc (模板不存在: $src)"
        return 1
    fi
}

print_header

# 创建 tasks 目录
if [ ! -d "tasks" ]; then
    mkdir -p tasks
    echo -e "  ${GREEN}✓${NC}  创建 tasks/ 目录"
    ((CREATED++))
else
    echo -e "  ${YELLOW}⏭${NC}  tasks/ 目录 (已存在，跳过)"
    ((SKIPPED++))
fi

# 复制并处理模板
echo ""
echo -e "${BLUE}创建核心文件：${NC}"
echo ""

copy_template "$SKILL_DIR/assets/CLAUDE.md.template" "CLAUDE.md" "CLAUDE.md       - AI上下文指南"
copy_template "$SKILL_DIR/assets/PROGRESS-LOG.md.template" "PROGRESS-LOG.md" "PROGRESS-LOG.md - 进度日志（倒序追加）"
copy_template "$SKILL_DIR/assets/TASKS.md.template" "tasks/TASKS.md" "tasks/TASKS.md  - 任务管理"
copy_template "$SKILL_DIR/assets/self.opt.template" "self.opt" "self.opt        - 经验沉淀"

# 输出结果
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}✅ PDCA 开发规范已建立！${NC}"
echo ""
echo -e "📊 统计：创建了 ${GREEN}$CREATED${NC} 个文件，跳过 ${YELLOW}$SKIPPED${NC} 个文件"
echo ""
echo -e "📁 文件说明："
echo ""
echo -e "   ${BLUE}CLAUDE.md${NC}       AI上下文指南，含PDCA流程和最佳实践"
echo -e "   ${BLUE}PROGRESS-LOG.md${NC} 进度日志，${YELLOW}倒序追加${NC}新记录"
echo -e "   ${BLUE}tasks/TASKS.md${NC}  任务管理，跟踪状态和优先级"
echo -e "   ${BLUE}self.opt${NC}        经验沉淀，记录错误模式和最佳实践"
echo ""
echo -e "📝 ${GREEN}下一步：${NC}"
echo ""
echo "   1. 编辑 tasks/TASKS.md 定义第一个任务"
echo "   2. 开始 PDCA 循环开发！"
echo ""
echo -e "💡 ${BLUE}提示：${NC}"
echo ""
echo "   • 运行 'cat CLAUDE.md' 查看完整使用指南"
echo "   • 每天开始工作前运行 'cat tasks/TASKS.md | grep -A 10 \"当前 Sprint\"'"
echo "   • 遇到错误及时记录到 self.opt"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
