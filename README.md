# Claude Skills Pool

这是一个个人 Claude Code 技能（Skills）和配置的集合仓库。旨在模块化管理不同的 AI 辅助能力，方便按需部署到不同的开发项目中。

## 📁 目录结构

项目的核心位于 `skills.claude/` 目录下，每个子文件夹代表一个独立的技能模块：

```text
.
├── LICENSE
├── README.md
├── CLAUDE.md               # 包含本项目开发规范的元文档
└── skills.claude/          # 技能池根目录
    ├── ai-spec/            # [编程策略] 将需求转为技术规范
    ├── code-debugger/      # [调试开发] 上下文优先的精准调试与增量开发
    ├── extract/            # [知识提取] 从内容抽提研究思路
    ├── ralph/              # [迭代开发] 基于PRD的循环工作流
    ├── research-analyst/   # [金融分析] 多Agent分析师团队
    └── ...
```

## 🚀 使用方法

要在一个新的项目中使用这里的某个技能：

1. 找到你需要的技能目录，例如 `skills.claude/ai-spec`。
2. 将该目录下的 `.claude` 文件夹完整复制到你的目标项目根目录。
   - 如果目标项目已有 `.claude` 目录，请合并内容（注意不要覆盖重要的 `settings.json`，主要是合并 `commands/` 和 `skills/`）。
3. 在目标项目中重启 Claude Code 终端。
4. 使用对应的 slash command (如 `/ai-spec`) 即可激活。

## 🛠️ 开发指南

如果你需要让 Claude Code 帮你在这个仓库中创建新技能，请参考 [CLAUDE.md](CLAUDE.md) 中的详细规范。

核心逻辑是：
1. **Command** (`.claude/commands/`): 定义用户输入的命令接口。
2. **Skill** (`.claude/skills/`): 定义核心 Prompt 和处理逻辑。
3. **Agent** (`.claude/agents/`): (可选) 定义复杂任务中的多角色 Agent。

## 📦 现有技能列表

| 技能名称 | 目录 | 描述 | 核心命令 |
| :--- | :--- | :--- | :--- |
| **编程策略工具** | `ai-spec` | 全栈架构师模式，将自然语言需求转化为生产级技术规范和 AI 执行指令 | `/ai-spec` |
| **智能调试助手** | `code-debugger` | 基于深度上下文理解的精准调试与增量开发，模块隔离防止连锁错误 | `/debug` |
| **思路抽提** | `extract` | 从杂乱文本中抽提结构化的研究思路和指令提示词 | `/extract` |
| **Ralph 工作流** | `ralph` | 这是一个根据 PRD 进行多轮迭代工作的自动化 Agent 流程 | `/ralph` |
| **金融分析师团队** | `research-analyst-system` | 包含首席分析师及多个细分领域专家的多 Agent 系统 | `/research` |
| **PubMed Linker** | `ref-pubmed-linker` | 自动处理和更新 PubMed 引用链接 | `/update-pubmed-links` |
