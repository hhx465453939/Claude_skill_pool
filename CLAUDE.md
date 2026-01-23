# CLAUDE.md - 开发规范与元指令

本文件定义了 `Claude Skills Pool` 项目的开发规范。当你（Claude Code）被要求创建、修改或分析本仓库中的技能时，必须严格遵守以下逻辑。

## 1. 项目核心逻辑

这是一个 **Claude Configuration Factory**。每个子目录（如 `skills.claude/xxx`）本质上都是一个独立的配置包，旨在被复制到其他项目的根目录下作为 `.claude` 目录使用。

因此，所有技能必须包含标准的 `.claude` 目录结构。

## 2. 标准目录结构 (Standard Directory Structure)

当用户要求"创建一个新技能 [SkillName]"时，请初始化以下结构：

```text
skills.claude/[SkillName]/          # 技能根目录 (建议使用英文 kebab-case)
└── .claude/
    ├── commands/                   # 存放 Slash Command 定义
    │   └── [command_name].md       # 对应 /command_name
    ├── skills/                     # 存放核心 Prompt/Skill 定义
    │   └── [skill_id].md           # 技能的具体实现
    ├── agents/                     # (可选) 存放子 Agent 定义
    │   └── [agent_name].md
    └── settings.local.json         # (可选) 局部配置文件
```

## 3. 文件格式规范

### 3.1 Commands (`.claude/commands/*.md`)
定义用户如何调用技能。通常是一个简单的 Markdown 文件，指向 Skill 或 Agent。

**模板:**
```markdown
---
description: [简短描述这个命令的作用]
---

# [Command Name]

[详细描述命令的行为]

使用方式:
1. 确保已加载相关 skill
2. 执行逻辑...
```

### 3.2 Skills (`.claude/skills/*.md`)
定义技能的核心 System Prompt。这是智能的核心。

**模板:**
```markdown
---
description: [技能描述]
---

# [Role Name]

你现在是 [角色名称]。

## 任务
[详细的任务描述]

## 约束
- [约束 1]
- [约束 2]

## 输出格式
[定义输出的 Markdown 格式]
```

### 3.3 Agents (`.claude/agents/*.md`)
用于定义更复杂的、有特定职责的 Agent（如 `research-analyst-system` 中的做法）。

## 4. 开发工作流 (Development Workflow)

当用户指令涉及"新建技能"或"更新技能"时，请执行以下步骤：

1.  **确认需求**:
    *   技能名称是什么？
    *   希望用什么 Slash Command 触发（例如 `/audit`）？
    *   技能的核心逻辑或 Prompt 是什么？

2.  **创建结构**:
    *   在 `skills.claude/` 下创建对应文件夹。
    *   构建 `.claude/commands` and `.claude/skills` 目录。

3.  **生成文件**:
    *   编写 `commands/[cmd].md`: 确保它能引导用户或直接调用 Skill。
    *   编写 `skills/[skill].md`: 根据用户需求编写高质量的 Prompt。

4.  **验证**:
    *   检查路径是否为绝对结构：`skills.claude/[name]/.claude/...`

## 5. 示例参考

在生成代码前，参考现有优秀的实现：
*   **简单单体 Skill**: 参考 `skills.claude/ai-spec` (包含 command 和 skill)
*   **复杂多 Agent 系统**: 参考 `skills.claude/research-analyst-system`
*   **配置驱动型**: 参考 `skills.claude/ralph`

## 6. 注意事项
*   **不要** 修改根目录的 `.claude`（除非是维护本项目自身）。
*   所有新技能都必须放在 `skills.claude/` 目录下。
*   文件名尽量使用英文 kebab-case (如 `my-cool-tool`)。
