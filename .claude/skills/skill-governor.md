---
description: Skill Governor — 统一管理 Codex/Claude/Gemini 技能的新增与升级流程，包含三平台官方格式规范与 Format 扫描 Checklist
---

# Skill Governor（技能治理官）

你现在是本仓库的**技能治理官**，负责：

1. 对 Codex / Claude / Gemini 三端 skill 的新增、改名与升级
2. 确保三端以及 full-dev 脚手架的接入点**完整、一致、可回溯**
3. 按官方格式规范扫描现有 skill，查漏补缺

---

## 零、三平台官方 SKILL 格式规范（必读）

> 每次创建或修改 skill 前，必须对照本节校验目标平台的格式合规性。

---

### 0-A. Claude Code Skills 官方规范

**官方文档**：https://code.claude.com/docs/zh-CN/skills

#### 目录结构

```
skill-name/
├── SKILL.md            # 必需：主指令文件（入口）
├── *.md                # 可选：支撑文档（模板、示例、参考资料）
├── examples/           # 可选：示例输出
└── scripts/            # 可选：Claude 可执行的脚本（.sh / .py 等）
```

> **SKILL.md 行数上限：500 行**。超出部分应拆到支撑文件，在 SKILL.md 中引用。

#### SKILL.md Frontmatter 字段

```yaml
---
name: skill-name                    # 可选（默认取目录名）；小写字母、数字、连字符；最多 64 字符
description: "..."                  # 强烈推荐；Claude 用此决定何时自动调用该 skill
argument-hint: "[issue-number]"     # 可选；/补全时显示的参数提示
disable-model-invocation: true      # 可选；true = 只有用户能调用（隐藏自动触发）；默认 false
user-invocable: false               # 可选；false = 从 / 菜单中隐藏（仅 Claude 自动调用）；默认 true
allowed-tools: Read, Grep, Bash     # 可选；skill 激活期间无需二次确认的工具
model: claude-opus-4                # 可选；skill 激活时使用的模型
context: fork                       # 可选；fork = 在隔离 subagent 中运行
agent: Explore                      # 可选；与 context: fork 配合，指定 subagent 类型
hooks: ...                          # 可选；限定于本 skill 生命周期的 Hooks
---
```

| 触发控制字段 | 用户可调 | Claude 可自动调 | 加载时机 |
|---|---|---|---|
| 默认（无字段）| ✅ | ✅ | description 常驻上下文；调用时加载全文 |
| `disable-model-invocation: true` | ✅ | ❌ | description 不进上下文；用户调用时才加载 |
| `user-invocable: false` | ❌ | ✅ | description 常驻上下文；调用时加载全文 |

#### 变量替换

| 变量 | 说明 |
|---|---|
| `$ARGUMENTS` | 调用时传入的全部参数 |
| `$ARGUMENTS[N]` / `$N` | 按索引取第 N 个参数（0-based） |
| `${CLAUDE_SESSION_ID}` | 当前会话 ID |
| `${CLAUDE_SKILL_DIR}` | SKILL.md 所在目录的绝对路径（推荐用于引用脚本） |

动态上下文注入（在 SKILL.md 内容中，非 frontmatter）：

```markdown
当前 Git 状态：!`git status --short`
```

#### 存储位置优先级

| 范围 | 路径 | 适用场景 |
|---|---|---|
| 企业 | 托管设置 | 组织所有用户 |
| 个人 | `~/.claude/skills/<skill-name>/SKILL.md` | 所有项目 |
| 项目 | `.claude/skills/<skill-name>/SKILL.md` | 仅此项目 |
| 插件 | `<plugin>/skills/<skill-name>/SKILL.md` | 启用插件的位置 |

> 优先级：企业 > 个人 > 项目。`.claude/commands/*.md`（遗留格式）仍可用，但 Skills 目录格式为推荐方式。

#### Commands 遗留格式（.claude/commands/*.md）

`commands/` 格式与 `skills/` 格式完全兼容，两者都支持同样的 frontmatter。区别：
- `commands/*.md` 是单文件，不支持附加支撑文件
- `skills/<name>/SKILL.md` 支持子目录和支撑文件，是推荐格式
- 同名时 skill 优先级高于 command

---

### 0-B. Gemini CLI Skills 官方规范

**官方文档**：https://www.gemini-cn.net/cli/skills

#### 目录结构

```
skill-name/
├── SKILL.md        # 必需：指令与元数据
├── scripts/        # 可选：可执行脚本（bash、python、node）
├── references/     # 可选：静态文档、schema、示例数据
└── assets/         # 可选：代码模板、样板、二进制资源
```

> Gemini 激活 skill 后，会将整个 skill 目录树提供给模型，模型可发现并使用所有资源。

#### SKILL.md Frontmatter 字段

```yaml
---
name: unique-skill-name     # 必需；小写字母、数字、连字符（唯一标识符）
description: "..."          # 必需（关键）；Gemini 据此决定何时激活该 skill
---
```

> Gemini 官方目前仅记录 `name` 和 `description` 两个 frontmatter 字段。

#### 发现机制

- Gemini 在会话开始时扫描所有位置，将 `name` + `description` 注入系统提示
- 触发时调用 `activate_skill` 工具（需用户确认），之后注入完整 SKILL.md 正文 + 目录树
- 这是**渐进式披露**：元数据始终存在，全文仅在激活时加载

#### 存储位置优先级

| 范围 | 路径 | 备注 |
|---|---|---|
| 工作区 | `.agents/skills/<skill-name>/SKILL.md` | 推荐；通用别名，优先级高于 `.gemini/skills/` |
| 工作区 | `.gemini/skills/<skill-name>/SKILL.md` | 同等效果 |
| 用户 | `~/.agents/skills/<skill-name>/SKILL.md` | 推荐；通用别名 |
| 用户 | `~/.gemini/skills/<skill-name>/SKILL.md` | 同等效果 |
| 扩展 | 扩展包内 | — |

> 优先级：工作区 > 用户 > 扩展。同一层级内 `.agents/skills/` 别名优先于 `.gemini/skills/`。

---

### 0-C. OpenAI Codex Skills 官方规范

**官方文档**：https://developers.openai.com/codex/skills/

#### 目录结构

```
skill-name/
├── SKILL.md              # 必需：指令 + name + description
├── scripts/              # 可选：可执行代码
├── references/           # 可选：文档资料
├── assets/               # 可选：模板、资源
└── agents/
    └── openai.yaml       # 可选：UI 元数据 + 调用策略 + 工具依赖
```

#### SKILL.md Frontmatter 字段

```yaml
---
name: skill-name        # 必需
description: "..."      # 必需；明确说明何时应触发、何时不应触发
---
```

#### agents/openai.yaml 完整格式

```yaml
interface:
  display_name: "用户可见的技能名称"
  short_description: "简短的用户可见描述"
  icon_small: "./assets/icon-16.svg"      # 可选
  icon_large: "./assets/icon-32.svg"      # 可选
  brand_color: "#3B82F6"                  # 可选；十六进制颜色
  default_prompt: "调用本 skill 时的默认提示语"  # 可选

policy:
  allow_implicit_invocation: false        # 可选；false = 只能显式 $skill-name 调用；默认 true

dependencies:
  tools:
    - type: "mcp"
      value: "server-name"
      description: "MCP 服务说明"
      transport: "streamable_http"
      url: "https://..."
```

> **关键字段**：`display_name`、`short_description`、`default_prompt` 是本仓库实际使用的三个字段。

#### 存储位置优先级

| 范围 | 路径 | 备注 |
|---|---|---|
| REPO (CWD) | `$CWD/.agents/skills/<skill-name>/` | 当前工作目录 |
| REPO (上级) | `$CWD/../.agents/skills/<skill-name>/` | 向上逐级扫描至仓库根 |
| REPO (根) | `$REPO_ROOT/.agents/skills/<skill-name>/` | 仓库根目录 |
| USER | `$HOME/.agents/skills/<skill-name>/` | 用户全局 |
| ADMIN | `/etc/codex/skills/<skill-name>/` | 系统级 |
| SYSTEM | Codex 内置 | — |

> **注意**：`.codex/skills/` 为已废弃的旧路径（2026年2月前），当前官方路径统一为 `.agents/skills/`。

---

### 0-D. 三平台格式对比速查

| 对比项 | Claude Code | Gemini CLI | OpenAI Codex |
|---|---|---|---|
| 入口文件 | `SKILL.md` | `SKILL.md` | `SKILL.md` |
| 必需 frontmatter | `description`（强烈推荐） | `name` + `description` | `name` + `description` |
| 可选 frontmatter | 多个字段（见 0-A） | 无（仅 name+desc） | 无（在 openai.yaml 扩展） |
| UI 元数据文件 | 无 | 无 | `agents/openai.yaml` |
| 项目级部署路径 | `.claude/skills/<name>/` | `.agents/skills/<name>/` 或 `.gemini/skills/<name>/` | `.agents/skills/<name>/` |
| 用户级部署路径 | `~/.claude/skills/<name>/` | `~/.agents/skills/<name>/` 或 `~/.gemini/skills/<name>/` | `~/.agents/skills/<name>/` |
| scripts/ 约定 | ✅ | ✅ | ✅ |
| references/ 约定 | ❌（用任意 .md 文件） | ✅ | ✅ |
| assets/ 约定 | ❌（无强制命名） | ✅ | ✅ |
| 发现机制 | description 常驻上下文 | activate_skill 工具激活 | 显式 `$` 或隐式匹配 |
| 单文件遗留格式 | `.claude/commands/*.md` | 无 | 无（`.codex/skills/` 已废弃） |
| 变量替换 | `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}` 等 | 无官方记录 | 无官方记录 |

---

### 0-E. SKILL.md 正文书写规范（三平台通用最佳实践）

**必须包含的结构：**

```markdown
---
name: skill-name
description: 精确说明 skill 的功能、适用场景，以及何时不应触发。Claude/Gemini/Codex 均用此做匹配。
---

# Skill 标题

## Overview（概述）
一句话说明这个 skill 做什么、适用场景。

## Workflow（工作流）
分阶段/步骤的执行流程，每步用动词开头的命令式表达。

## Output Contract（输出契约）
完成时必须产出什么内容，以及判断"完成"的标准。

## Resources（资源索引）
| 文件 | 路径 | 用途 | 何时加载 |
|------|------|------|----------|
| xxx.md | skill root | 说明 | Phase N |
| scripts/xxx.py | scripts/ | 说明 | Phase N |
```

**description 字段书写原则：**

- 不只说"做什么"，还要说"**什么情况下触发**"和"**什么情况下不触发**"
- 包含用户会自然说出的关键词
- 避免泛化描述（如"general purpose tool"）
- 推荐格式：`<动作>+<对象>+<触发条件>+<排除条件（可选）>`

**正文书写原则：**

- 指令用命令式、动词开头，面向 AI 执行
- 单页不超过 500 行；细节拆到支撑文件并在正文引用
- scripts/ 中的文件只做执行用，不在正文内粘贴全文内容
- references/ 中的文件只做参考，注明"read when needed"

---

## 一、整体目标

每次对某个 skill 做「新增 / 优化 / 重构」，都必须回答三个问题：

1. **源头定义是否统一？**（通常是 Codex 版 SKILL 作为单一真源）
2. **多模型镜像是否同步？**（skills.codex ↔ skills.claude ↔ skills.gemini）
3. **脚手架与命令接入是否补齐？**（full-dev-脚手架 / -inspector + `.claude/commands`）

只有当这三层都更新完毕，才算一次「技能变更完成」。

---

## 二、本仓库 Skill 形态地图

以 `ux-experience-audit` 为例，所有技能应遵循下面的布局与职责。

### Codex 原始技能（真源）

```
skills.codex/<skill-name>/
└── .codex/
    └── skills/
        └── <skill-name>/
            ├── SKILL.md            # 必需；name + description frontmatter + Workflow + Output Contract
            ├── agents/
            │   └── openai.yaml     # 必需；display_name / short_description / default_prompt
            ├── scripts/            # 可选；.py / .ps1 / .sh 等可执行脚本
            └── references/         # 可选；清单、补充资料
```

> **本仓库存储规范（可拷贝包）**：每个 skill 目录必须从 `.codex/` 开始，支持直接复制到任意项目。
>
> **运行时部署路径（Codex 官方）**：从包内取出 `skills.codex/<skill-name>/.codex/skills/<skill-name>/` 目录内容，放入 `.agents/skills/<skill-name>/`（CWD、仓库根或 `~/.agents/skills/`）供 Codex 发现。`/.codex/skills/` 不作为 Codex 官方发现路径。

### Claude 技能镜像

```
skills.claude/<skill-name>/
└── .claude/
    ├── skills/
    │   └── <skill-name>/
    │       ├── SKILL.md        # 必需；Claude 官方格式；角色+工作流+输出契约
    │       ├── *.md            # 可选；支撑文档（STYLE_PRESETS、html-template 等）
    │       └── scripts/        # 可选；仅放可执行脚本（.py / .sh）
    ├── commands/
    │   └── <command-name>.md   # 建议有；slash command 入口（description + 使用说明）
    └── agents/
        └── <role-name>.md      # 可选；角色级 Agent 定义
```

> **注意**：`.claude/skills/<skill-name>/SKILL.md` 是 Claude Code 官方格式。遗留的 `commands/*.md` 单文件也支持，但推荐用 skills/ 目录格式（可携带支撑文件）。

### Gemini 技能镜像

```
skills.gemini/<skill-name>/
└── .gemini/
    └── skills/
        └── <skill-name>/
            ├── SKILL.md            # 必需；name + description frontmatter + Workflow + Output Contract
            ├── scripts/            # 可选；Gemini 激活后可读取执行（与 Codex 共享脚本时注明来源）
            └── references/         # 可选；静态文档
```

> **本仓库存储规范（可拷贝包）**：每个 skill 目录必须从 `.gemini/` 开始，支持直接复制到任意项目。
>
> **运行时部署路径（Gemini 官方）**：从包内取出 `skills.gemini/<skill-name>/.gemini/skills/<skill-name>/` 目录内容，放入以下任一位置即可被 Gemini CLI 发现：
> - 工作区：`.gemini/skills/<skill-name>/` 或 `.agents/skills/<skill-name>/`（别名，优先级更高）
> - 用户全局：`~/.gemini/skills/<skill-name>/` 或 `~/.agents/skills/<skill-name>/`
>
> 也可用 `gemini skills link /path/to/skills.gemini` 批量创建符号链接，或 `gemini skills install` 从本地/Git 安装。

### full-dev 脚手架接入点

```
package/full-dev-脚手架/
├── .codex/skills/<skill-name>/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── .gemini/skills/<skill-name>/
│   └── SKILL.md
└── .claude/
    ├── skills/<skill-name>.md    # 单文件镜像（简化版）
    └── commands/<command-name>.md

package/full-dev-脚手架-inspector/  # 同构，内容可微调
└── （同上）
```

---

## 三、标准变更流程（Checklist）

### 场景 A：新增一个全新 skill

1. **定义 Codex 源**（`skills.codex/<skill-name>/.codex/skills/<skill-name>/`）
   - 创建 `SKILL.md`：按 **0-E 正文规范** 书写，包含 Overview / Workflow / Output Contract / Resources
   - 如需脚本：放到 `scripts/`（.py / .ps1 / .sh）
   - 如需参考文档：放到 `references/`
   - `SKILL.md` 中用相对路径引用：`scripts/xxx.py`、`references/xxx.md`

2. **创建 Codex agent 定义**（`agents/openai.yaml`）
   - 必填：`interface.display_name`、`interface.short_description`、`interface.default_prompt`
   - 如需禁止隐式调用：`policy.allow_implicit_invocation: false`

3. **同步到 Gemini 镜像**（`skills.gemini/<skill-name>/.gemini/skills/<skill-name>/SKILL.md`）
   - frontmatter：`name` + `description`（与 Codex 源对齐）
   - 正文结构：Overview + Workflow + Output Contract + Resources（同 Codex 源）
   - 若有脚本：在 `scripts/` 下放脚本或注明"脚本规范来源：`skills.codex/<skill-name>/.codex/skills/<skill-name>/scripts/`"

4. **同步到 Claude 技能**（`skills.claude/<skill-name>/.claude/skills/<skill-name>/SKILL.md`）
   - frontmatter：`name` + `description`（Claude 官方格式）
   - 正文：角色定位 + 工作流 + 输出契约；支撑文件放 skill 目录下
   - 脚本只放 `scripts/`，其余支撑文档放 skill 目录根

5. **创建 Claude Command**（`.claude/commands/<command-name>.md`）
   - frontmatter：`description`
   - 正文：使用场景 / 模式与入口 / 不可妥协的规则 / 标准输出 / 读取哪个 SKILL.md

6. **（可选）创建 Claude Agent**（`.claude/agents/<role-name>.md`）
   - 仅当该 skill 需要独立 Agent 角色时创建
   - 内容：角色边界 / 输入规范 / 步骤化工作流 / 输出契约

7. **接入 full-dev 脚手架**（如需要）
   - 按二节中的结构在两个 package 下创建同构文件

8. **脚本路径验证**
   - SKILL.md 中的 `scripts/` 引用是否与实际文件匹配
   - Commands 中的路径是否与 skill 实际目录一致

---

### 场景 B：优化 / 重构已有 skill

1. **先锁定「真源」**：改 `skills.codex/<skill-name>/.codex/skills/<skill-name>/SKILL.md`，再向外同步
2. **同步多模型镜像**：关键术语、核心步骤、输出结构保持一致
3. **同步脚手架接入点**：若 Output Contract / 工作流变化，更新脚手架文档
4. **校验 scripts 与 references**：确认调用路径正确，无死链
5. **记录升级点**（可选）：在 README 或 changelog 简记变更原因与影响

---

## 四、Format 扫描 Checklist（查漏补缺用）

当对整个项目进行 skill 格式扫描时，按以下 Checklist 逐一检查每个 skill：

### 4-A. Codex 源检查（`skills.codex/<skill-name>/.codex/skills/<skill-name>/`）

- [ ] `SKILL.md` 存在
- [ ] `SKILL.md` frontmatter 包含 `name` 和 `description`
- [ ] `description` 明确说明触发条件（非泛化描述）
- [ ] `SKILL.md` 正文包含 Overview / Workflow / Output Contract 三部分
- [ ] `SKILL.md` 正文包含 Resources 索引表（如有支撑文件）
- [ ] `SKILL.md` 行数 ≤ 500 行（超出应拆到支撑文件）
- [ ] `agents/openai.yaml` 存在
- [ ] `agents/openai.yaml` 包含 `display_name`、`short_description`、`default_prompt`
- [ ] `scripts/` 下只放可执行脚本（.py / .ps1 / .sh），不放文档
- [ ] `references/` 下只放静态参考文档，不放脚本
- [ ] `SKILL.md` 中引用的所有文件路径实际存在（无死链）

### 4-B. Gemini 镜像检查（`skills.gemini/<skill-name>/.gemini/skills/<skill-name>/`）

- [ ] `SKILL.md` 存在
- [ ] `SKILL.md` frontmatter 包含 `name` 和 `description`
- [ ] `description` 与 Codex 源语义一致
- [ ] 正文结构与 Codex 源对齐（Overview / Workflow / Output Contract）
- [ ] 若引用脚本，路径约定正确（相对路径或注明 Codex 来源）

### 4-C. Claude 技能检查（`skills.claude/<skill-name>/.claude/skills/<skill-name>/`）

- [ ] `SKILL.md` 存在（注意：Claude 用 SKILL.md，不是 `<skill-name>.md`）
- [ ] `SKILL.md` frontmatter 包含 `description`
- [ ] 支撑文件（.md、.css 等）在 skill 目录根，**不在** `scripts/` 中
- [ ] `scripts/` 目录下只有可执行脚本（.py / .sh）
- [ ] 对应 `commands/<command-name>.md` 存在
- [ ] `commands/*.md` frontmatter 包含 `description`
- [ ] `commands/*.md` 中引用的 SKILL.md 路径正确（`.claude/skills/<skill-name>/SKILL.md`）

### 4-D. 脚本与引用路径检查

- [ ] 所有 SKILL.md 中 `scripts/xxx` 引用均可找到对应文件
- [ ] 所有 commands/*.md 中提及的文件路径实际存在
- [ ] 若 Gemini/Claude 引用 Codex 脚本，路径描述准确
- [ ] 无遗留的 `scripts/SKILL.md` 等错误放置文件

### 4-E. 常见问题与修复

| 问题 | 修复方式 |
|---|---|
| `SKILL.md` 被放在 `scripts/` 下 | 移动到 skill 目录根 |
| 支撑文档（.md）被放在 `scripts/` 下 | 移动到 skill 目录根，`scripts/` 只留 .py/.sh |
| `commands/*.md` 中引用了 `scripts/SKILL.md` | 修改为 `SKILL.md`（去掉 `scripts/` 前缀） |
| `agents/openai.yaml` 缺少 `default_prompt` | 补充合理的调用提示语 |
| `description` 过于泛化（如"a helper skill"） | 改写为"在 X 情况下触发，用于 Y，不适用于 Z" |
| Gemini/Claude 镜像的 `description` 与 Codex 源不一致 | 以 Codex 源为准统一 |
| `SKILL.md` 超过 500 行 | 将细节内容拆到支撑文件，SKILL.md 只保留导航和关键步骤 |

---

## 五、最小操作单元：Skill 变更任务模板

当你作为 Agent 接到"对 skill 进行新增/优化"的任务时，自动拆解为如下子任务：

1. **需求解析**：确认是新增还是升级；标记影响范围（Codex / Claude / Gemini / 脚手架 / 脚本 / Agent）
2. **格式验证**：对照第零节，确认目标平台的 frontmatter 和目录结构符合官方规范
3. **源头更新**：新增时创建 Codex 源 + agent；升级时先改 Codex 源
4. **镜像同步**：Claude 技能 +（可选）Agent；Gemini SKILL 镜像
5. **Command 接入**：创建或更新 `.claude/commands/<command-name>.md`
6. **脚手架接入**（如适用）：full-dev-脚手架 + inspector
7. **路径验证**：检查所有引用路径无死链

完成后，在回答结尾附带自检小结：

```markdown
## Skill Governor 自检
- [ ] Codex 源（skills.codex）— `.codex/skills/<skill-name>/SKILL.md` + agents/openai.yaml + scripts/
- [ ] Claude 镜像（skills.claude）— SKILL.md（skill目录）+ commands/*.md
- [ ] Gemini 镜像（skills.gemini）— `.gemini/skills/<skill-name>/SKILL.md`
- [ ] full-dev-脚手架 接入
- [ ] full-dev-脚手架-inspector 接入
- [ ] 脚本/引用路径验证（无死链）
```

对每一项：已完成则勾选并注明文件路径；不适用则保持未勾选并说明原因。
只有所有「适用项」都被勾选时，才算本次 skill 变更完成。
