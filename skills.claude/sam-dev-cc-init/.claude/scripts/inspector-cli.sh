#!/bin/bash

# Inspector Agent CLI - Display feedback for Worker/Inspector/Human synchronization
# Usage: ./inspector-cli.sh [command] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/.inspector-log.txt"
STATE_FILE="${PROJECT_ROOT}/.inspector-state.json"

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ============================================================================
# Display Functions
# ============================================================================

show_header() {
    echo -e "${BOLD}${BLUE}"
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│         PDCO Inspector Agent - Feedback Dashboard           │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

show_agent_status() {
    local grade=$1
    local points=$2
    local budget_level=$3
    local efficiency=$4
    
    echo -e "${BOLD}[AGENT STATUS]${NC}"
    echo "├─ Current Grade: $(get_grade_emoji "$grade") $grade"
    echo "├─ Points: ${CYAN}${points}${NC}"
    echo "├─ Budget Level: $(get_budget_emoji "$budget_level") $budget_level"
    echo "└─ Token Efficiency: ${GREEN}${efficiency}%${NC}"
    echo ""
}

get_grade_emoji() {
    case $1 in
        A) echo "✨" ;;
        B) echo "👍" ;;
        C) echo "⚠️ " ;;
        D) echo "❌" ;;
        *) echo "?" ;;
    esac
}

get_budget_emoji() {
    case $1 in
        "Strict") echo "🔴" ;;
        "Standard") echo "🟡" ;;
        "Generous") echo "🟢" ;;
        "Trust") echo "🔵" ;;
        *) echo "?" ;;
    esac
}

show_evaluation_excellent() {
    local consecutive_a=$1
    local avg_efficiency=$2
    local next_upgrade=$3
    local challenge_level=$4
    
    echo -e "${GREEN}${BOLD}[EVALUATION] Agent Performance: EXCELLENT${NC}"
    echo "├─ Status: ✅ All metrics exceed expectations"
    echo "├─ Consecutive A-grades: ${consecutive_a}"
    echo "├─ Avg Token efficiency: ${avg_efficiency}%"
    echo "├─ CHECKFIX compliance: 100%"
    echo "│"
    echo "├─ 📈 Trajectory:"
    echo "│  ├─ Quality: ↗ Improving"
    echo "│  ├─ Efficiency: ↗ Optimized"
    echo "│  └─ Self-correction: ↗ Excellent"
    echo "│"
    echo "├─ 🎯 Next Milestone:"
    echo "│  ├─ Required: ${next_upgrade} more A-grades to upgrade"
    echo "│  └─ Recommended: Challenge level → ${challenge_level}"
    echo "│"
    echo "└─ ⚡ Action: Proceed to next task"
    echo ""
}

show_alert_pattern() {
    local pattern=$1
    local occurrences=$2
    local severity=$3
    local risk_level=$4
    
    echo -e "${YELLOW}${BOLD}[ALERT] Pattern Detected: Quality Regression${NC}"
    echo "├─ Pattern: ${pattern}"
    echo "├─ Occurrences: ${occurrences} times"
    echo "├─ Severity: ${severity}"
    echo "├─ Risk Level: ${risk_level}"
    echo "│"
    echo "├─ 🔍 Root Cause Hypothesis:"
    echo "│  ├─ [ ] Cause 1 (Likelihood: High)"
    echo "│  ├─ [ ] Cause 2 (Likelihood: Medium)"
    echo "│  └─ [ ] Cause 3 (Likelihood: Low)"
    echo "│"
    echo "├─ ⚡ Required Actions (Priority):"
    echo "│  ├─ [URGENT] Review self.opt entries"
    echo "│  ├─ [HIGH] Modify DO phase checklist"
    echo "│  └─ [MEDIUM] Review token estimation"
    echo "│"
    echo "├─ 🛡️  Prevention Strategy:"
    echo "│  ├─ Next task: Apply {measures}"
    echo "│  ├─ Weekly: Compare to baseline"
    echo "│  └─ Escalation: If pattern persists"
    echo "│"
    echo "└─ Current Status: MEDIUM RISK - Intervention required"
    echo ""
}

show_critical_rework() {
    local issue=$1
    local severity=$2
    local deadline=$3
    local estimated_tokens=$4
    
    echo -e "${RED}${BOLD}[CRITICAL] Task Delivery: REWORK REQUIRED${NC}"
    echo "├─ Grade: ❌ C (Rework needed)"
    echo "├─ Primary Issue: ${issue}"
    echo "├─ Severity: ${severity}"
    echo "├─ Estimated Token Cost: ${estimated_tokens}k"
    echo "│"
    echo "├─ 📋 Rework Requirements:"
    echo "│  ├─ [ ] Fix primary issue"
    echo "│  ├─ [ ] Run CHECKFIX [8/8]"
    echo "│  ├─ [ ] Document in self.opt"
    echo "│  └─ [ ] Submit for re-review"
    echo "│"
    echo "├─ ⏰ Deadline: ${deadline}"
    echo "├─ Budget Impact: Downgrade to 🟡 Standard (8k)"
    echo "├─ Cooldown: 3 tasks (no upgrade eligible)"
    echo "├─ Points: -20"
    echo "│"
    echo "├─ 🎯 Recovery Target:"
    echo "│  └─ Achieve A-grade within next 3 deliveries"
    echo "│"
    echo "└─ Required Self-Analysis:"
    echo "   ├─ [ ] Root cause in self.opt"
    echo "   ├─ [ ] Prevention trigger defined"
    echo "   └─ [ ] Historical patterns reviewed"
    echo ""
}

show_warning_degradation() {
    local issue_count=$1
    local points_lost=$2
    
    echo -e "${RED}${BOLD}[CRITICAL ALERT] Quality Degradation Detected${NC}"
    echo "├─ Issues Found: ${issue_count}"
    echo "├─ Points Lost: ${points_lost}"
    echo "├─ Current Risk Level: HIGH"
    echo "│"
    echo "├─ 🚨 MANDATORY IMPROVEMENT PLAN (Non-negotiable):"
    echo "│  ├─ [1] CHECKFIX Compliance (Critical)"
    echo "│  │   ├─ Requirement: 8/8 pass rate EVERY delivery"
    echo "│  │   ├─ Rule: Zero exceptions, zero shortcuts"
    echo "│  │   ├─ Penalty for skip: -50 points per incident"
    echo "│  │   └─ Target: Achieve [8/8] in next 3 deliveries"
    echo "│  │"
    echo "│  ├─ [2] Error Documentation (Critical)"
    echo "│  │   ├─ Requirement: Every error → self.opt entry"
    echo "│  │   ├─ Format: Issue → Root cause → Solution"
    echo "│  │   └─ Purpose: Prevent recurring patterns"
    echo "│  │"
    echo "│  └─ [3] Token Estimation Accuracy (High)"
    echo "│      ├─ Requirement: Estimate ±20% of actual"
    echo "│      ├─ Buffer: Add 20% to complex tasks"
    echo "│      └─ Target: >80% estimation accuracy"
    echo "│"
    echo "├─ 🔧 System Actions (Auto-Applied):"
    echo "│  ├─ ✓ Budget downgrade: 🔴 Strict (3k tokens)"
    echo "│  ├─ ✓ Review level: MANDATORY 2-tier review"
    echo "│  ├─ ✓ Points: -50"
    echo "│  └─ ✓ Escalation: Deep diagnostic if continues"
    echo "│"
    echo "└─ ⚠️  Risk: Continued degradation → Task suspension"
    echo ""
}

# ============================================================================
# Commands
# ============================================================================

cmd_status() {
    show_header
    show_agent_status "A" "125" "Generous" "92"
    echo -e "${CYAN}Last evaluation: $(date)${NC}"
    echo ""
}

cmd_feedback() {
    local feedback_type=${1:-excellent}
    
    show_header
    
    case $feedback_type in
        excellent)
            show_evaluation_excellent "2" "88" "1" "Hard"
            ;;
        alert)
            show_alert_pattern "Code complexity increasing" "3" "MEDIUM" "MEDIUM"
            ;;
        rework)
            show_critical_rework "Architectural design flaw" "HIGH" "2026-02-17 18:00" "9"
            ;;
        warning)
            show_warning_degradation "3" "50"
            ;;
        *)
            echo "Unknown feedback type: $feedback_type"
            exit 1
            ;;
    esac
}

cmd_dashboard() {
    local agent=${1:-all}
    
    show_header
    
    if [[ "$agent" == "all" || "$agent" == "frontend" ]]; then
        echo -e "${BOLD}[Frontend Agent - Status]${NC}"
        show_agent_status "A" "145" "Generous" "94"
        echo ""
    fi
    
    if [[ "$agent" == "all" || "$agent" == "backend" ]]; then
        echo -e "${BOLD}[Backend Agent - Status]${NC}"
        show_agent_status "B" "87" "Standard" "81"
        echo ""
    fi
    
    if [[ "$agent" == "all" || "$agent" == "analyst" ]]; then
        echo -e "${BOLD}[Analyst Agent - Status]${NC}"
        show_agent_status "A" "128" "Generous" "88"
        echo ""
    fi
    
    if [[ "$agent" == "all" ]]; then
        echo -e "${BOLD}[GLOBAL TEAM METRICS]${NC}"
        echo "├─ Total Agents: 3"
        echo "├─ Avg Grade: A- (across all agents)"
        echo "├─ Team Token Efficiency: 87%"
        echo "├─ Avg CHECKFIX Compliance: 97%"
        echo "├─ Weekly Points Trend: ↗ +89 pts"
        echo "└─ Risk Agents: 0"
        echo ""
        
        echo -e "${BOLD}[RECENT EVALUATIONS (All Agents)]${NC}"
        echo "├─ Frontend: Task UI refactor → ✨ A grade | +15 points"
        echo "├─ Backend: API design → 👍 B grade | +7 points"
        echo "├─ Analyst: Data analysis → ✨ A grade | +15 points"
        echo "└─ System: Average efficiency improved +6%"
        echo ""
        
        echo -e "${BOLD}[UPCOMING MILESTONES]${NC}"
        echo "├─ Backend: Fix {issue} → Upgrade to 🟢 Generous"
        echo "├─ Analyst: 1 more A-grade → Reach 🔵 Trust level"
        echo "└─ System: Achieve 90% team efficiency target"
        echo ""
    fi
}

cmd_sync() {
    local component=${1:-all}
    
    show_header
    
    echo -e "${BOLD}[SYNCHRONIZATION STATUS]${NC}"
    echo ""
    
    case $component in
        worker|all)
            echo -e "${GREEN}✓ Worker Agent${NC}"
            echo "  ├─ Last update: $(date)"
            echo "  ├─ Budget level synced: 🟡 Standard (8k)"
            echo "  ├─ Current task: In progress (DO phase)"
            echo "  └─ Estimated completion: 2h"
            echo ""
            ;;
    esac
    
    case $component in
        inspector|all)
            echo -e "${GREEN}✓ Inspector Agent${NC}"
            echo "  ├─ Last evaluation: $(date -v-5m)"
            echo "  ├─ Feedback generated: Pattern Alert"
            echo "  ├─ Next check: 30min"
            echo "  └─ Status: Monitoring"
            echo ""
            ;;
    esac
    
    case $component in
        human|all)
            echo -e "${GREEN}✓ Human Dashboard${NC}"
            echo "  ├─ Last refresh: $(date)"
            echo "  ├─ Notifications: 2 pending"
            echo "  │  ├─ Pattern Alert (Medium)"
            echo "  │  └─ Token Efficiency Update"
            echo "  └─ Status: Updated"
            echo ""
            ;;
    esac
}

cmd_log() {
    show_header
    
    echo -e "${BOLD}[INSPECTION LOG]${NC}"
    echo ""
    echo "[2026-02-15 14:23] EVALUATION: Task completed - Grade A"
    echo "[2026-02-15 14:20] CHECKFIX: All 8 items passed"
    echo "[2026-02-15 14:15] DO: Code implementation phase"
    echo "[2026-02-15 14:00] PLAN: Task started"
    echo "[2026-02-14 16:45] EVALUATION: Task completed - Grade B"
    echo "[2026-02-14 16:40] CHECKFIX: 7/8 items passed"
    echo "[2026-02-14 16:35] WARNING: Pattern detected in error handling"
    echo ""
}

cmd_compare() {
    show_header
    
    echo -e "${BOLD}[WORKER PERFORMANCE COMPARISON]${NC}"
    echo ""
    echo "Previous 5 Tasks:"
    printf "%-15s %-12s %-15s %-12s\n" "Task" "Grade" "Efficiency" "Points"
    echo "─────────────────────────────────────────────────────────"
    printf "%-15s %-12s %-15s %-12s\n" "Bug Fix" "A" "75%" "+15"
    printf "%-15s %-12s %-15s %-12s\n" "API Endpoint" "B" "88%" "+7"
    printf "%-15s %-12s %-15s %-12s\n" "Refactor" "A" "92%" "+15"
    printf "%-15s %-12s %-15s %-12s\n" "Test Suite" "C" "65%" "-20"
    printf "%-15s %-12s %-15s %-12s\n" "Documentation" "B" "78%" "+7"
    echo ""
    echo -e "Trend: ${YELLOW}⚠️  Slight degradation${NC} (C grade detected)"
    echo "Action: Review pattern, apply prevention measures"
    echo ""
}

# ============================================================================
# Help
# ============================================================================

show_help() {
    cat << EOF
${BOLD}Inspector Agent CLI - PDCO Global Management System${NC}

Usage: ./inspector-cli.sh [command] [options]

Commands (Single Agent):
  status [agent]      Show agent status
                      Agents: frontend|backend|analyst|designer|tester|...
  feedback [type]     Show feedback (excellent|alert|rework|warning)
  dashboard [agent]   Show dashboard for specific agent
  log [agent]         Show inspection log for agent

Commands (Global):
  dashboard all       Show all agents status + team metrics
  sync [component]    Show sync status (worker|inspector|human|all)
  teams               Show team-wide analysis and comparisons
  risks               Show risk alerts across all agents
  compare             Compare performance across agents
  help                Show this help message

Examples:
  # Single agent
  ./inspector-cli.sh status frontend
  ./inspector-cli.sh dashboard backend
  ./inspector-cli.sh feedback excellent
  
  # Global view
  ./inspector-cli.sh dashboard all
  ./inspector-cli.sh teams
  ./inspector-cli.sh risks
  ./inspector-cli.sh compare

Environment:
  LOG_FILE:   ${LOG_FILE}
  STATE_FILE: ${STATE_FILE}

Architecture:
  L0: Inspector Agent (Global supervisor)
  L1: Skill Agents (Frontend/Backend/Analyst/Designer/Tester/...)
  L2: Sync Layer (Worker-Inspector-Human)

Three-way Synchronization:
  Worker Agents → Execute tasks, generate logs
  Inspector Agent → Evaluate all agents, generate feedback
  Human → Monitor via CLI, make decisions

EOF
}

# ============================================================================
# Main
# ============================================================================

main() {
    local cmd=${1:-status}
    
    case $cmd in
        status)
            cmd_status
            ;;
        feedback)
            cmd_feedback "$2"
            ;;
        dashboard)
            cmd_dashboard
            ;;
        sync)
            cmd_sync "$2"
            ;;
        log)
            cmd_log
            ;;
        compare)
            cmd_compare
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            echo "Unknown command: $cmd"
            echo "Use './inspector-cli.sh help' for usage"
            exit 1
            ;;
    esac
}

main "$@"
