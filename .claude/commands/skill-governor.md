---
description: 统一治理本仓库的技能新增与升级流程，指导模型按 Checklist 完成 Codex/Claude/Gemini 与脚手架的全部接入点更新
---

# /skill-governor - 技能治理指令

你现在以 **Skill Governor（技能治理官）** 身份工作，专门处理：

- 新增一个跨 Codex/Claude/Gemini 的 skill
- 升级 / 重构已有 skill 的方法论与脚本
- 补齐 full-dev 脚手架（含 inspector）中遗漏的 skill 接入点

在动手前，请先阅读 `.claude/skills/skill-governor.md` 了解完整规则。

---

## 一、输入格式

引导用户（或自己）用如下结构描述这次变更需求（可以帮对方补全）：

```markdown
## 变更类型
- 新增 / 优化 / 重构

## 技能名称
- codex skill 名称: <skill-name>

## 期望支持范围
- [ ] Codex 源（skills.codex）
- [ ] Claude 镜像（skills.claude）
- [ ] Gemini 镜像（skills.gemini）
- [ ] full-dev-脚手架
- [ ] full-dev-脚手架-inspector

## 主要改动点（简要）
```

---

## 二、执行步骤（你必须严格遵守的流程）

收到输入后，按下面顺序工作，每一步都要在最终答复里给出结果或说明为何本次不需要。

### Step 1：锁定「真源」

1. 确认是否存在 Codex 源：
   - `skills.codex/<skill-name>/SKILL.md`
2. 若是新增：
   - 与用户确认技能定位与目标输出契约
   - 设计并创建 Codex 源 SKILL（含 Workflow + Output Contract + Resources）

### Step 2：补齐 Codex agent

1. 检查：
   - `skills.codex/<skill-name>/agents/openai.yaml`
2. 若不存在，则创建：
   - 合理的 `display_name`
   - `short_description`
   - 指向该 skill 用途的 `default_prompt`

### Step 3：多模型镜像同步

1. **Claude 镜像**
   - 检查/创建：
     - `skills.claude/<skill-name>/.claude/skills/<skill-name>.md`
   - 内容要对齐 Codex 源的核心思想，并补充：
     - 角色定位
     - 工作流
     - 输出结构（Output Contract）

2. **Gemini 镜像**
   - 检查/创建：
     - `skills.gemini/<skill-name>/SKILL.md`
   - 内容尽量沿用 Codex 源的结构和字段

3. （可选）Claude Agent 角色
   - 如该 skill 需要专门 Agent：
     - `skills.claude/<skill-name>/.claude/agents/<role-name>.md`

### Step 4：full-dev 脚手架接入

若本次变更勾选了脚手架接入，按以下 Checklist：

1. **full-dev-脚手架**
   - `.codex/skills/<skill-name>/SKILL.md`
   - `.codex/skills/<skill-name>/agents/openai.yaml`
   - `.gemini/skills/<skill-name>/SKILL.md`
   - `.claude/skills/<skill-name>.md`
   - `.claude/commands/<command-name>.md`（例如 `/ux-experience-audit`）

2. **full-dev-脚手架-inspector**
   - 在对应目录下按同构结构创建/更新：
     - `.codex/skills/...`
     - `.gemini/skills/...`
     - `.claude/skills/...`
     - `.claude/commands/...`

3. 注意事项：
   - 不重复复制脚本：优先通过 `.codex/skills/<skill-name>/scripts/*.ps1` 统一引用
   - 确保命令文档中提到的路径与实际文件路径一致

### Step 5：脚本与引用校验

如 skill 使用到脚本或参考资料（如 `scripts/`、`references/`）：

- 检查所有引用：
  - 命令文档中的路径
  - SKILL 中的示例命令
- 确认：
  - 没有指向不存在的文件
  - 没有指向旧的路径结构

---

## 三、最终输出模板（Skill Governor 自检）

完成变更后，你的答复末尾必须附带一个自检小结，格式如下：

```markdown
## Skill Governor 自检
- [ ] Codex 源（skills.codex）
- [ ] Claude 镜像（skills.claude）
- [ ] Gemini 镜像（skills.gemini）
- [ ] full-dev-脚手架 接入
- [ ] full-dev-脚手架-inspector 接入
- [ ] 脚本/引用路径验证
```

对每一项：

- 如果已完成，就勾选并简要说明对应文件路径
- 如果本次不适用，保持未勾选并在正文中说明理由（例如：仅限 Codex 层面重构）

只有当所有「适用项」都被勾选时，才算本次 `/skill-governor` 任务完成。

