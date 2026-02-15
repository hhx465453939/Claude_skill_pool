#!/bin/bash
# PDCA 完成检查脚本
# 检查今日任务是否完成，进度日志是否更新

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TODAY=$(date +%Y-%m-%d)
CHECKS_PASSED=0
CHECKS_TOTAL=0

check() {
    ((CHECKS_TOTAL++))
    local desc="$1"
    local condition="$2"
    
    if eval "$condition"; then
        echo -e "  ${GREEN}✓${NC} $desc"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "  ${RED}✗${NC} $desc"
        return 1
    fi
}

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}        📋 PDCA 完成检查                                  ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "检查日期：${GREEN}$TODAY${NC}"
echo ""

# 检查文件存在性
echo -e "${BLUE}文件检查：${NC}"
check "CLAUDE.md 存在" "[ -f CLAUDE.md ]"
check "PROGRESS-LOG.md 存在" "[ -f PROGRESS-LOG.md ]"
check "tasks/TASKS.md 存在" "[ -f tasks/TASKS.md ]"
check "self.opt 存在" "[ -f self.opt ]"

echo ""
echo -e "${BLUE}今日进度检查：${NC}"

# 检查今日是否有进度记录
if [ -f "PROGRESS-LOG.md" ]; then
    if head -20 PROGRESS-LOG.md | grep -q "$TODAY"; then
        check "今日进度已记录" "true"
    else
        check "今日进度已记录" "false"
        echo -e "     ${YELLOW}提示：在 PROGRESS-LOG.md 顶部添加今日记录${NC}"
    fi
else
    check "今日进度已记录" "false"
fi

# 检查是否有 IN_PROGRESS 任务
if [ -f "tasks/TASKS.md" ]; then
    IN_PROGRESS_COUNT=$(grep -c "IN_PROGRESS" tasks/TASKS.md 2>/dev/null || echo 0)
    if [ "$IN_PROGRESS_COUNT" -gt 0 ]; then
        check "当前有进行中的任务 ($IN_PROGRESS_COUNT 个)" "true"
    else
        check "当前有进行中的任务" "false"
        echo -e "     ${YELLOW}提示：从 tasks/TASKS.md 领取新任务${NC}"
    fi
    
    # 检查是否有 DONE 任务
    DONE_COUNT=$(grep -c "DONE" tasks/TASKS.md 2>/dev/null || echo 0)
    if [ "$DONE_COUNT" -gt 0 ]; then
        check "有已完成的任务 ($DONE_COUNT 个)" "true"
    else
        check "有已完成的任务" "false"
    fi
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 计算通过率
if [ $CHECKS_TOTAL -gt 0 ]; then
    PERCENTAGE=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))
    
    if [ $PERCENTAGE -eq 100 ]; then
        echo -e "${GREEN}✅ 所有检查通过！PDCA 循环运转良好。${NC}"
    elif [ $PERCENTAGE -ge 70 ]; then
        echo -e "${YELLOW}⚠️  大部分检查通过 ($CHECKS_PASSED/$CHECKS_TOTAL)，还有改进空间。${NC}"
    else
        echo -e "${RED}❌ 需要关注 ($CHECKS_PASSED/$CHECKS_TOTAL)，请完善 PDCA 流程。${NC}"
    fi
fi

echo ""
