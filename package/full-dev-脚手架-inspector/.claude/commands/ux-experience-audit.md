---
description: UX Experience Audit - 从用户旅程出发的跨层体验审计与修复闭环
---

# /ux-experience-audit - 用户体验审计（Inspector 版）

你现在激活了 **UX Experience Audit（用户体验审计）** 流程，专门处理“功能看似完成但体验不通”的问题，适配 full-dev-脚手架-inspector 的项目结构。

> 建议先阅读 `.claude/skills/ux-experience-audit.md` 获取完整方法论。

---

## 适用场景

- 配置改了没反应、按钮点了没反馈、状态不清楚
- 模型/供应商切换失败，但错误信息不清晰
- 复制/导出等关键操作经常报错或静默失败
- 用户能勉强完成任务，但觉得“很难用/不可信”

不适合：

- 纯代码级 Bug 修复（建议先 `/debug`）
- 纯视觉/UI 美化（建议用 `/debug-ui`）

---

## 标准工作流程（结合 Inspector 脚手架）

### 1. 构建用户旅程地图

引导用户用句式重述问题：

```text
用户在 <步骤> 做 <动作> 后，预期 <结果>，实际 <结果>
```

并标出：

- 所在页面或模块（web 前端、ui 组件、inspector 扩展视图等）
- 操作路径：从进入页面到出问题的完整步骤
- 每一步的可见信号：按钮/Toast/加载/错误提示/网络请求

### 2. 运行 UX 命令审计（依赖 Codex skill 脚本）

本脚手架已经引入了 Codex 版 `ux-experience-audit` 脚本，可以直接在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File .codex/skills/ux-experience-audit/scripts/ux-audit.ps1 -Mode scan -ProjectRoot .
```

或按需引导执行核心扫描命令：

```powershell
rg -n "provider|baseURL|model|apiKey|loadModels|testConnection|chatStream|handleCopy|useMessage" packages
rg -n "@click|@copy|@send|message\.success|message\.error|warning\(" packages/web/src packages/ui/src
rg -n "TODO|FIXME|HACK|XXX" packages docs
```

你的任务：

- 结合扫描结果，按模块聚合潜在 UX 断点
- 标记典型问题：配置不生效、交互无反馈、错误静默/误导、链路断裂等

### 3. 按 UX 影响度排序

使用统一优先级：

- `P0`：阻断主流程（无法配置/无法发送/数据丢失/核心按钮崩溃）
- `P1`：高摩擦（可绕过但频繁失败、错误提示不清、结果不可信）
- `P2`：体验优化（文案/默认值/交互一致性/辅助反馈）

在同一模块内，**先清零 P0，再处理 P1/P2**。

### 4. 设计最小跨层修复

- 以“用户可感知路径”为边界，而不是前端/后端/配置的团队边界
- 每次只修一条体验链路（例如：从“点击发送”到“看到结果/错误”的链路）
- 典型改动：
  - 文案改进，说明当前状态和下一步操作
  - 补充 Loading/Disabled/重试逻辑
  - 修正前后端字段或状态不一致导致的“成功无反馈/错误静默”
  - 配置默认值、空值保护、回退策略

### 5. 执行 Checkfix 闭环

在有改动的前后端模块上执行至少一类自动检查（build/lint/test 任一）；推荐直接使用脚本的 `full` 模式：

```powershell
powershell -ExecutionPolicy Bypass -File .codex/skills/ux-experience-audit/scripts/ux-audit.ps1 -Mode full -ProjectRoot .
```

- 检查通过：记录命令与结果，作为本轮体验修复的验证依据
- 检查失败：当轮尽量给出修复建议，无法立即解决的记为技术债并标明优先级

### 6. 同步 .debug 与 docs

- `.debug/<module>-debug.md`：
  - 补充：问题、根因、改动、验证步骤与结果、影响评估
- `docs/`：
  - 若前端体验可见变化：为零基础用户补充操作步骤、常见问题与回滚方式
  - 若涉及配置/API/环境：更新相关部署/配置文档

---

## 输出格式（强约束）

完成 `/ux-experience-audit` 后，输出内容应遵循：

```markdown
## 用户问题重述
## 体验断点地图
## 根因与优先级（P0/P1/P2）
## 修复与改动文件
## 验证命令与结果
## 文档与.debug更新
## 残留风险与下一步
```

---

## 用户输入

请按下面格式描述你现在遇到的体验问题（可以粗略写，我会帮你结构化）：

```markdown
## 当前场景

## 体验问题
用户在 <步骤> 做 <动作> 后，预期 <结果>，实际 <结果>

## 涉及模块/页面
```

