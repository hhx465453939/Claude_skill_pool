#!/bin/bash
# Session Catchup - 会话恢复脚本
# 在恢复工作、长时间会话后或上下文重置后运行

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}        🔄 会话恢复 - Session Catchup                     ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 5-Question Reboot Test
echo -e "${BLUE}5-Question Reboot Test:${NC}"
echo ""

echo -e "${YELLOW}Q1: Where am I?${NC}"
if [ -f "tasks/TASKS.md" ]; then
    CURRENT_PHASE=$(grep -A 1 "当前阶段" tasks/TASKS.md | tail -1 | sed 's/当前阶段：//' | xargs)
    if [ -n "$CURRENT_PHASE" ]; then
        echo -e "   → 当前阶段：${GREEN}$CURRENT_PHASE${NC}"
    else
        echo -e "   → ${YELLOW}查看 tasks/TASKS.md 了解当前阶段${NC}"
    fi
else
    echo -e "   → ${YELLOW}tasks/TASKS.md 不存在${NC}"
fi

echo ""
echo -e "${YELLOW}Q2: Where am I going?${NC}"
if [ -f "tasks/TASKS.md" ]; then
    echo -e "   → 查看 ${GREEN}tasks/TASKS.md${NC} 的「当前 Sprint」和「待办池」"
else
    echo -e "   → ${YELLOW}tasks/TASKS.md 不存在${NC}"
fi

echo ""
echo -e "${YELLOW}Q3: What's the goal?${NC}"
if [ -f "tasks/TASKS.md" ]; then
    GOAL=$(grep -A 1 "项目目标" tasks/TASKS.md | tail -1 | xargs)
    if [ -n "$GOAL" ] && [ "$GOAL" != "[一句话描述项目最终目标]" ]; then
        echo -e "   → ${GREEN}$GOAL${NC}"
    else
        echo -e "   → ${YELLOW}查看 tasks/TASKS.md 的项目目标部分${NC}"
    fi
else
    echo -e "   → ${YELLOW}tasks/TASKS.md 不存在${NC}"
fi

echo ""
echo -e "${YELLOW}Q4: What have I learned?${NC}"
if [ -f "self.opt" ]; then
    LEARN_COUNT=$(grep -c "^### 法则" self.opt 2>/dev/null || echo 0)
    ERROR_COUNT=$(grep -c "^### " self.opt 2>/dev/null || echo 0)
    echo -e "   → 查看 ${GREEN}self.opt${NC} ($LEARN_COUNT 条法则，$(($ERROR_COUNT - $LEARN_COUNT)) 个错误模式)"
else
    echo -e "   → ${YELLOW}self.opt 不存在${NC}"
fi

echo ""
echo -e "${YELLOW}Q5: What have I done?${NC}"
if [ -f "PROGRESS-LOG.md" ]; then
    LAST_DATE=$(head -10 PROGRESS-LOG.md | grep -E "^## [0-9]{4}-[0-9]{2}-[0-9]{2}" | head -1 | sed 's/## //' | xargs)
    if [ -n "$LAST_DATE" ]; then
        echo -e "   → 最后记录：${GREEN}$LAST_DATE${NC}"
    else
        echo -e "   → 查看 ${GREEN}PROGRESS-LOG.md${NC}"
    fi
else
    echo -e "   → ${YELLOW}PROGRESS-LOG.md 不存在${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 快速状态摘要
echo -e "${BLUE}快速状态摘要：${NC}"
echo ""

# 当前进行中的任务
if [ -f "tasks/TASKS.md" ]; then
    echo -e "${YELLOW}进行中的任务：${NC}"
    grep "IN_PROGRESS" tasks/TASKS.md | head -3 | while read line; do
        TASK_NAME=$(echo "$line" | awk -F'|' '{print $2}' | xargs)
        echo -e "   • $TASK_NAME"
    done
    IN_PROGRESS_COUNT=$(grep -c "IN_PROGRESS" tasks/TASKS.md 2>/dev/null || echo 0)
    if [ "$IN_PROGRESS_COUNT" -eq 0 ]; then
        echo -e "   ${YELLOW}（无）${NC}"
    fi
fi

echo ""

# 最近的进度
echo -e "${YELLOW}最近的进度：${NC}"
if [ -f "PROGRESS-LOG.md" ]; then
    # 提取第一个日期条目下的今日完成
    head -30 PROGRESS-LOG.md | grep -E "^- \*\*今日完成" -A 10 | head -15 || echo -e "   ${YELLOW}（查看 PROGRESS-LOG.md 获取详情）${NC}"
else
    echo -e "   ${YELLOW}PROGRESS-LOG.md 不存在${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "💡 ${GREEN}建议的下一步：${NC}"
echo ""

if [ -f "tasks/TASKS.md" ]; then
    IN_PROGRESS_COUNT=$(grep -c "IN_PROGRESS" tasks/TASKS.md 2>/dev/null || echo 0)
    if [ "$IN_PROGRESS_COUNT" -gt 0 ]; then
        echo -e "   1. 继续当前进行中的任务"
        echo -e "   2. 完成后更新 PROGRESS-LOG.md 和 tasks/TASKS.md"
    else
        echo -e "   1. 从 tasks/TASKS.md 领取新任务"
        echo -e "   2. 更新任务状态为 IN_PROGRESS"
    fi
else
    echo -e "   1. 初始化 PDCA 工作流"
    echo -e "   2. 运行 sam-init 或 pdca"
fi

echo ""
echo -e "   查看 CLAUDE.md 了解完整 PDCA 流程"
echo ""
