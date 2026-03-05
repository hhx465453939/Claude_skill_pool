---
name: ux-experience-audit
description: 从用户使用体验而非单层技术实现角度，执行问题扫描、优先级判定与修复闭环。用于“功能看似可用但体验不通”的场景，例如配置后不生效、交互无反馈、错误提示误导、跨前后端链路断裂、模型/供应商切换失败、复制导出等关键操作报错。
---

# UX Experience Audit

## Overview

用用户旅程驱动排查与修复：先确认“用户哪里卡住”，再映射到代码链路，最后用命令闭环验证并同步文档。

## Workflow

### 1) Build User Journey Map

- 定义失败路径：进入页面 → 配置 → 执行动作 → 接收反馈 → 继续下一步。
- 记录每个节点的“可见信号”：按钮状态、Toast、加载态、错误文本、网络请求。
- 将问题表述为体验语句：`用户在 <步骤> 做 <动作> 后，预期 <结果>，实际 <结果>`。

### 2) Run Command Audit

优先运行脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .codex/skills/ux-experience-audit/scripts/ux-audit.ps1 -Mode scan -ProjectRoot .
```

或手动运行核心扫描命令：

```powershell
rg -n "provider|baseURL|model|apiKey|loadModels|testConnection|chatStream|handleCopy|useMessage" packages
rg -n "@click|@copy|@send|message\.success|message\.error|warning\(" packages/web/src packages/ui/src
rg -n "TODO|FIXME|HACK|XXX" packages docs
```

### 3) Prioritize by UX Impact

按下面优先级排序：

- `P0`: 阻断主流程（无法配置、无法发送、数据丢失、核心按钮崩溃）
- `P1`: 高摩擦（可绕过但频繁失败、错误提示不清、结果不可信）
- `P2`: 体验优化（文案、默认值、交互一致性、辅助反馈）

### 4) Implement Minimal Cross-Layer Fix

- 优先修复“用户可感知路径”上的断点，不按前后端边界分割任务。
- 保持最小改动：每次只改一条体验链路，避免引入并发回归。
- 增加防错：默认值、空值保护、提示文本、回退策略。

### 5) Execute Checkfix Loop

运行全量闭环：

```powershell
powershell -ExecutionPolicy Bypass -File .codex/skills/ux-experience-audit/scripts/ux-audit.ps1 -Mode full -ProjectRoot .
```

至少保证一个自动检查通过（build/lint/test 任一类），并记录失败原因与后续计划。

### 6) Sync Debug + Docs

- 更新 `.debug/<module>-debug.md`：问题、根因、改动、验证、影响。
- 前端体验变更必须更新 `docs/`，面向零基础用户写可执行步骤。
- 涉及配置/环境/API 的改动，补充故障排查和回滚说明。

## Output Contract

完成任务时输出以下结构：

```markdown
## 用户问题重述
## 体验断点地图
## 根因与优先级（P0/P1/P2）
## 修复与改动文件
## 验证命令与结果
## 文档与.debug更新
## 残留风险与下一步
```

## Resources

- `scripts/ux-audit.ps1`: 一键执行 UX 扫描与 checkfix 命令。
- `references/ux-checklist.md`: 体验检查清单与常见反模式。

