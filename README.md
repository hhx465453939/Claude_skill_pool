# AI Skills Pool

这是一个个人 AI 编程工具技能（Skills）和配置的集合仓库。旨在模块化管理不同的 AI 辅助能力，方便按需部署到不同的开发项目中。

目前支持四个平台：**Claude Code**（`skills.claude/`）、**OpenAI Codex**（`skills.codex/`）、**Gemini CLI**（`skills.gemini/`）和 **Cursor**（`.cursor/rules/`）。

---

## 📁 目录结构

```text
.
├── LICENSE
├── README.md
├── CLAUDE.md                    # Claude Code 开发规范元文档（本仓库自身）
│
├── skills.claude/               # Claude Code 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   ├── ref-pubmd-linker/        # [文献] PubMed 引用链接查询与更新
│   ├── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│   └── update-pubmed-links/     # [文献] PubMed 链接批量更新（变体）
│
├── skills.codex/                # OpenAI Codex 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── pubmed-linker/           # [文献] PubMed 引用链接查询与更新
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   └── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│
├── skills.gemini/               # Gemini CLI 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── prd/                     # [需求文档] 结构化 PRD 生成
│   ├── pubmed-linker/           # [文献] PubMed 引用链接查询与更新
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   ├── ralph-yolo/              # [迭代开发] Ralph 全自动模式
│   └── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│
├── package/                     # 预打包的脚手架（多技能一体化部署）
│   └── full-dev-脚手架/         # 全栈开发环境脚手架
│       ├── CLAUDE.md            # Claude Code 初始化引导
│       ├── AGENTS.md            # Codex 初始化引导
│       ├── GEMINI.md            # Gemini CLI 初始化引导
│       ├── .claude/             # Claude Code 完整配置（8 commands + 8 skills + 3 agents）
│       ├── .codex/              # Codex 技能包（5 skills）
│       ├── .gemini/             # Gemini CLI 技能包（7 skills）
│       └── .cursor/             # Cursor 规则（2 rules）
│
└── .cursor/                     # 本仓库自身的 Cursor 规则
    └── rules/
        ├── api-first-development.mdc
        └── project-structure.mdc
```

---

## 🚀 使用方法

### 方式一：单技能部署（按需挑选）

适合只需要特定能力的场景。

#### Claude Code

1. 在 `skills.claude/` 中找到需要的技能目录，例如 `skills.claude/code-debugger/`。
2. 将目录下的 `.claude/` 文件夹完整复制到目标项目根目录。
   - 若项目已有 `.claude/` 目录，合并 `commands/` 和 `skills/` 子目录（注意不要覆盖已有的 `settings.json`）。
3. 重启 Claude Code 终端，使用对应的 slash command（如 `/debug`）激活。

#### OpenAI Codex

1. 在 `skills.codex/` 中找到需要的技能目录，例如 `skills.codex/code-debugger/`。
2. 将目录下的 `.codex/` 文件夹完整复制到目标项目根目录。
   - 若项目已有 `.codex/` 目录，合并 `skills/` 子目录。
3. 在 Codex 中使用 `$skill-name`（如 `$code-debugger`）激活。

#### Gemini CLI

1. 在 `skills.gemini/` 中找到需要的技能目录，例如 `skills.gemini/code-debugger/`。
2. 将目录下的 `SKILL.md` 文件复制到目标项目的 `.gemini/skills/[skill-name]/` 目录。
   - 若目录不存在，创建 `.gemini/skills/[skill-name]/` 后再复制。
3. Gemini CLI 会根据任务描述自动匹配并触发对应技能。

### 方式二：脚手架一键部署（推荐全栈项目使用）

适合需要完整 AI 辅助开发环境的全栈项目，一次部署即可让 Claude Code、Codex、Gemini CLI、Cursor 四个工具同时获得全套开发能力。

1. 将 `package/full-dev-脚手架/` 目录下的内容复制到目标项目根目录：

   ```bash
   # 方法一：完全替换（推荐新项目）
   cp -r package/full-dev-脚手架/* /path/to/your-project/
   cp -r package/full-dev-脚手架/.[a-z]* /path/to/your-project/
   
   # 方法二：增量合并（推荐有存量代码的项目）
   # 复制文档
   cp package/full-dev-脚手架/{CLAUDE,AGENTS,GEMINI}.md /path/to/your-project/
   
   # 创建并复制配置目录内容
   mkdir -p /path/to/your-project/.claude
   cp -r package/full-dev-脚手架/.claude/* /path/to/your-project/.claude/
   
   mkdir -p /path/to/your-project/.codex
   cp -r package/full-dev-脚手架/.codex/* /path/to/your-project/.codex/
   
   mkdir -p /path/to/your-project/.gemini
   cp -r package/full-dev-脚手架/.gemini/* /path/to/your-project/.gemini/
   
   mkdir -p /path/to/your-project/.cursor
   cp -r package/full-dev-脚手架/.cursor/* /path/to/your-project/.cursor/
   ```

2. 部署后目标项目的结构：

   ```text
   your-project/
   ├── CLAUDE.md        ← Claude Code 读取，显示可用 commands 和核心规范
   ├── AGENTS.md        ← Codex 读取，显示可用 skills 和核心约束
   ├── GEMINI.md        ← Gemini CLI 读取，显示可用 skills 和使用方式
   ├── .claude/         ← Claude Code：/sam-init, /ai-spec, /api-first, /debug, /debug-ui, /prd, /ralph, /ralph-yolo
   ├── .codex/          ← Codex：$ai-spec, $api-first-modular, $code-debugger, $debug-ui, $ralph
   ├── .gemini/         ← Gemini CLI：ai-spec, api-first-modular, code-debugger, debug-ui, prd, ralph, ralph-yolo
   ├── .cursor/         ← Cursor：API-First 开发规则自动生效
   └── (your code...)
   ```

3. 打开项目后：
    - **第一步**：执行 `/sam-init` 初始化项目 PDCA 工作流（生成 CLAUDE.md、PROGRESS-LOG.md、tasks/TASKS.md、self.opt）
    - **Claude Code**：输入 `/` 查看所有可用命令
    - **Codex**：自动根据任务触发对应技能，或使用 `$skill-name` 手动触发
    - **Gemini CLI**：描述意图即可自动匹配技能
    - **Cursor**：规则自动生效，无需手动操作

**⚠️ 注意**：在本仓库（Claude_skill_pool）中测试 Inspector CLI：
```bash
# 方式1: 相对路径 (在项目根目录)
bash skills.claude/sam-dev-cc-init/.claude/scripts/inspector-cli.sh dashboard

# 方式2: 部署到实际项目后
# 先将 package/full-dev-脚手架/ 或 skills.claude/sam-dev-cc-init/.claude/ 复制到目标项目根目录
# 然后在目标项目中运行:
./.claude/scripts/inspector-cli.sh dashboard
```

---

## 🛠️ 开发指南

如果你需要让 Claude Code 帮你在这个仓库中创建新技能，请参考 [CLAUDE.md](CLAUDE.md) 中的详细规范。

### Claude Code 技能结构

```text
skills.claude/[SkillName]/
└── .claude/
    ├── commands/[command].md    # Slash Command 定义
    ├── skills/[skill].md        # 核心 Prompt 和处理逻辑
    ├── agents/[agent].md        # (可选) 多角色 Agent
    └── settings.local.json      # (可选) 局部配置
```

### OpenAI Codex 技能结构

```text
skills.codex/[skill-name]/
└── .codex/
    └── skills/
        └── [skill-name]/
            ├── SKILL.md              # 核心 Skill 定义（含 YAML frontmatter）
            └── agents/
                └── openai.yaml       # 接口配置（display_name / short_description / default_prompt）
```

### Gemini CLI 技能结构

```text
skills.gemini/[skill-name]/
└── SKILL.md                          # 核心 Skill 定义（含 YAML frontmatter）
```

部署时复制到目标项目的 `.gemini/skills/[skill-name]/SKILL.md`。

### Cursor 规则结构

```text
.cursor/
└── rules/
    └── [rule-name].mdc              # Cursor Rule 定义（含 frontmatter: description, globs, alwaysApply）
```

---

## 📦 现有技能列表

### 编程与开发

| 技能名称 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :--- |
| **PDCA 工作流初始化 (sam-dev-cc-init)** | `/sam-init` | — | — | 为项目一键初始化 CLAUDE.md、PROGRESS-LOG.md、tasks/TASKS.md、self.opt（项目级自优化） |
| **编程策略工具 (ai-spec)** | `/ai-spec` | `$ai-spec` | ✓ | 全栈架构师模式，将自然语言需求转化为生产级技术规范和 AI 执行指令 |
| **API-First 模块化 (api-first-modular)** | `/api-first` | `$api-first-modular` | ✓ | 后端功能封装为独立 API 包，前端只调 API，跨层任务按 API 边界自动分解 |
| **智能调试助手 (code-debugger)** | `/debug` | `$code-debugger` | ✓ | 基于深度上下文理解的精准调试与增量开发，模块隔离防止连锁错误 |
| **UI 设计师 (debug-ui)** | `/debug-ui` | `$debug-ui` | ✓ | 顶级 UI 设计师模式，六维视觉诊断 + 像素级代码实施，与 debug 共享 `.debug/` 文档 |
| **PRD 生成器 (prd)** | `/prd` | — | ✓ | 交互式生成结构化产品需求文档 |
| **Ralph 工作流 (ralph)** | `/ralph` | `$ralph` | ✓ | 基于 PRD 的自主 Agent 循环，逐个实现 User Story 并自动提交 |
| **Ralph YOLO (ralph-yolo)** | `/ralph-yolo` | — | ✓ | Ralph 全自动模式，无人值守 |

### 科研与文献

| 技能名称 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :--- |
| **Dr. Midas (dr-midas)** | `/midas` | `$dr-midas` | ✓ | 科研炼金术士，分析科研图表并结合 PubMed 文献生成深度科研叙事 |
| **PubMed Linker** | `/update-pubmed-links` | `$pubmed-linker` | ✓ | 自动查询并更新参考文献的 PubMed 链接、PMID、DOI |
| **论文投稿管理 (paper-submission-manager)** | `/paper-submission-manager` | `$paper-submission-manager` | ✓ | 论文投稿全流程管理：清单、QA、材料打包与提交追踪 |

### 研究与分析

| 技能名称 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :--- |
| **思路抽提 (extract)** | `/extract` | `$extract` | ✓ | 从深度研究文档中反向提取可复用的研究方法论框架和 Prompt 模板 |
| **金融分析师团队 (research-analyst-system)** | `/research` | `$research-analyst-system` | ✓ | 首席分析师 + 6 大研究小组并行深度调研，输出结构化投资报告 |

### 脚手架

| 名称 | 包含工具 | 描述 |
| :--- | :---: | :--- |
| **全栈开发脚手架 (full-dev)** | Claude + Codex + Gemini + Cursor | 一键部署完整 AI 辅助全栈开发环境，含 7 个 Claude commands + 5 个 Codex skills + 7 个 Gemini skills + 2 条 Cursor rules |
