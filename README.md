<div align="center">
  <img src="assets/logo.png" alt="AI Skills Pool" width="128">
</div>

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
│   └── superpowers/              # Superpowers v2.0 泛用框架草稿
├── docs/                         # 参考文档（不参与脚手架执行）
│   └── inspector/                # Inspector 设计与场景说明
│       ├── INSPECTOR-CROSS-PLATFORM.md
│       ├── INSPECTOR-SCENARIO-WALKTHROUGH.md
│       └── README.md
│
├── skills.claude/               # Claude Code 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── comfyui-workflow-designer/ # [图像] ComfyUI / SD 工作流 JSON 设计与模型推荐
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── drawio-xml-roadmap/      # [设计] draw.io 路线图/流程图 XML 生成
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── frontend-slides/         # [前端演示] 单文件 HTML 演示文稿生成与 PPT 转换
│   ├── nodejs-npm-auto-release/ # [工程] Node.js npm 自动发版与 GitHub Actions
│   ├── office-docs/             # [办公] PPTX/DOCX/XLSX 读取、编辑、创建与校验
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── sci-journal-submission-expert/# [投稿] SCI 期刊全流程专家（预审、选刊、合规、审稿回复、APC）
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   ├── ref-pubmed-linker/       # [文献] PubMed 引用链接查询与更新（参考实现）
│   ├── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│   ├── sam-dev-cc-init/         # [工作流] PDCA 项目初始化（/sam-init）
│   ├── scrna-celltype-annotation/# [生信] 单细胞亚群细胞类型注释与报告
│   ├── shidianguji-fetcher/     # [古籍采集] 识典古籍批量下载与 Markdown 整理
│   ├── superpowers/             # [方法论] 泛用式 AI 任务处理框架（TDD + 系统化工作流）
│   ├── update-pubmed-links/     # [文献] PubMed 链接批量更新（命令变体）
│   └── ux-experience-audit/     # [体验] 用户体验问题扫描与修复闭环
│
├── skills.codex/                # OpenAI Codex 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── comfyui-workflow-designer/ # [图像] ComfyUI / SD 工作流 JSON 设计与模型推荐
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── drawio-xml-roadmap/      # [设计] draw.io 路线图/流程图 XML 生成
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── frontend-slides/         # [前端演示] 单文件 HTML 演示文稿生成与 PPT 转换
│   ├── inspector/               # [监管] PDCO 全局监管（Codex 版）
│   ├── nodejs-npm-auto-release/ # [工程] Node.js npm 自动发版
│   ├── office-docs/             # [办公] PPTX/DOCX/XLSX 读取、编辑、创建与校验
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── sci-journal-submission-expert/# [投稿] SCI 期刊全流程专家（预审、选刊、合规、审稿回复、APC）
│   ├── pubmed-linker/           # [文献] PubMed 引用链接查询与更新
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   ├── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│   ├── scrna-celltype-annotation/# [生信] 单细胞亚群细胞类型注释与报告
│   ├── shidianguji-fetcher/     # [古籍采集] 识典古籍批量下载与 Markdown 整理
│   ├── superpowers/             # [方法论] 泛用式 AI 任务处理框架（TDD + 系统化工作流）
│   └── ux-experience-audit/     # [体验] 用户体验问题扫描与修复闭环
│
├── skills.gemini/               # Gemini CLI 技能池（单技能独立部署）
│   ├── ai-spec/                 # [编程策略] 将需求转为技术规范
│   ├── api-first-modular/       # [架构框架] API-First 模块化开发
│   ├── code-debugger/           # [调试开发] 上下文优先的精准调试与增量开发
│   ├── comfyui-workflow-designer/ # [图像] ComfyUI / SD 工作流 JSON 设计与模型推荐
│   ├── debug-ui/                # [UI设计] 顶级 UI 设计师模式
│   ├── drawio-xml-roadmap/      # [设计] draw.io 路线图/流程图 XML 生成
│   ├── dr-midas/                # [科研] 科研炼金术士，图表分析与叙事
│   ├── extract/                 # [知识提取] 从内容抽提研究方法论框架
│   ├── frontend-slides/         # [前端演示] 单文件 HTML 演示文稿生成与 PPT 转换
│   ├── inspector/               # [监管] PDCO 全局监管（Gemini 版）
│   ├── nodejs-npm-auto-release/ # [工程] Node.js npm 自动发版
│   ├── office-docs/             # [办公] PPTX/DOCX/XLSX 读取、编辑、创建与校验
│   ├── paper-submission-manager/# [投稿管理] 论文投稿全流程管理与材料打包
│   ├── sci-journal-submission-expert/# [投稿] SCI 期刊全流程专家（预审、选刊、合规、审稿回复、APC）
│   ├── prd/                     # [需求文档] 结构化 PRD 生成
│   ├── pubmed-linker/           # [文献] PubMed 引用链接查询与更新
│   ├── ralph/                   # [迭代开发] 基于 PRD 的自主 Agent 循环
│   ├── ralph-yolo/              # [迭代开发] Ralph 全自动模式
│   ├── research-analyst-system/ # [金融分析] 多 Agent 分析师团队
│   ├── scrna-celltype-annotation/# [生信] 单细胞亚群细胞类型注释与报告
│   ├── shidianguji-fetcher/     # [古籍采集] 识典古籍批量下载与 Markdown 整理
│   ├── superpowers/             # [方法论] 泛用式 AI 任务处理框架（TDD + 系统化工作流）
│   └── ux-experience-audit/     # [体验] 用户体验问题扫描与修复闭环
│
├── package/                     # 预打包的脚手架（多技能一体化部署）
│   ├── enterprise-use/          # 企业咨询工具箱（6个核心咨询/文档技能）
│   │   ├── CLAUDE.md            # Claude Code 初始化引导
│   │   ├── AGENTS.md            # Codex 初始化引导
│   │   ├── GEMINI.md            # Gemini CLI 初始化引导
│   │   ├── .claude/             # Claude Code（6 commands + office-docs 脚本工具链）
│   │   ├── .codex/              # Codex 技能包（6 skills）
│   │   └── .gemini/             # Gemini CLI 技能包（6 skills）
│   ├── full-dev-脚手架/         # 全栈开发环境（仅开发技能，无 PDCA/Inspector）
│   │   ├── CLAUDE.md            # Claude Code 初始化引导
│   │   ├── AGENTS.md            # Codex 初始化引导
│   │   ├── GEMINI.md            # Gemini CLI 初始化引导
│   │   ├── .claude/             # Claude Code（8 commands + 9 skills）
│   │   ├── .codex/              # Codex 技能包（7 skills）
│   │   ├── .gemini/             # Gemini CLI 技能包（9 skills）
│   │   └── .cursor/             # Cursor 规则（2 rules）
│   └── full-dev-脚手架-inspector/ # 全栈开发 + PDCA/Inspector（含 /sam-init 与入职看板）
│       ├── CLAUDE.md
│       ├── AGENTS.md
│       ├── GEMINI.md
│       ├── .claude/             # 在 full-dev 基础上增加 sam-init、sam-dev-cc-init 及 PDCA 模板（9 commands + 10 skills）
│       ├── .codex/
│       ├── .gemini/
│       └── .cursor/
│
└── .cursor/                     # 本仓库自身的 Cursor 规则
    └── rules/
        ├── api-first-development.mdc
        └── project-structure.mdc
```

---

## 📖 参考文档

以下文档仅作**阅读与理解**用，不参与脚手架或脚本执行：

- **[docs/inspector/](docs/inspector/)** — Inspector Agent 跨平台架构与场景演示（从入职到专家的完整周期）。部署了 sam-dev-cc-init 或使用 Inspector CLI 时，可在此查阅设计与用法说明。

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
2. 将目录下的 `.codex/` 文件夹完整复制到目标项目根目录（若已有 `.codex/` 则合并 `skills/` 子目录）。
3. 在 Codex 中使用 `$skill-name`（如 `$code-debugger`）激活。

#### Gemini CLI

1. 在 `skills.gemini/` 中找到需要的技能目录，例如 `skills.gemini/code-debugger/`。
2. 将目录下的 `.gemini/` 文件夹完整复制到目标项目根目录（若已有 `.gemini/` 则合并 `skills/` 子目录）。
3. Gemini CLI 会根据任务描述自动匹配并触发对应技能。

### 方式二：脚手架一键部署（推荐多技能项目使用）

适合需要多技能一次打包部署的项目。可按场景选择全栈开发、企业咨询、或 Inspector 增强版本。

**三种脚手架如何选：**

| 脚手架 | 适用场景 | 区别摘要 |
|--------|----------|----------|
| **enterprise-use** | 企业咨询、管理决策、谈判推进、法务研判、Office/PDF 文档处理 | 业务咨询工具箱：executive-consultant、executive-secretary、external-negotiation-master、global-legal-counsel、office-docs、pdf-reader；不含 Cursor 规则与开发类技能 |
| **full-dev-脚手架** | 只要「需求→规范→开发→调试」全流程，不需要项目级 PDCA 与看板 | 仅开发技能：ai-spec、api-first、debug、debug-ui、prd、ralph 等，无 `/sam-init` |
| **full-dev-脚手架-inspector** | 需要 PDCA 循环、任务看板、进度日志与 Inspector 入职/专家周期管理 | 在 full-dev 基础上增加 `/sam-init`、sam-dev-cc-init、PROGRESS-LOG、tasks、self.opt 等，可与 [docs/inspector/](docs/inspector/) 配合使用 |

1. 将所选脚手架目录下的内容复制到目标项目根目录（下例以 `full-dev-脚手架` 为例，若选 inspector 则替换为 `full-dev-脚手架-inspector`）：

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

2. 部署后目标项目的结构（若使用 **full-dev-脚手架-inspector** 还会多出 `/sam-init` 及 PDCA 相关能力）：

   ```text
   your-project/
   ├── CLAUDE.md        ← Claude Code 读取，显示可用 commands 和核心规范
   ├── AGENTS.md        ← Codex 读取，显示可用 skills 和核心约束
   ├── GEMINI.md        ← Gemini CLI 读取，显示可用 skills 和使用方式
   ├── .claude/         ← Claude Code：/ai-spec, /api-first, /debug, /debug-ui, /prd, /ralph, /ralph-yolo, /ux-experience-audit（inspector 版另有 /sam-init）
   ├── .codex/          ← Codex：$ai-spec, $api-first-modular, $code-debugger, $debug-ui, $ralph
   ├── .gemini/         ← Gemini CLI：ai-spec, api-first-modular, code-debugger, debug-ui, prd, ralph, ralph-yolo
   ├── .cursor/         ← Cursor：API-First 开发规则自动生效
   └── (your code...)
   ```

3. 打开项目后：
    - **若使用 full-dev-脚手架-inspector**：第一步执行 `/sam-init` 初始化 PDCA 工作流（生成/更新 CLAUDE.md、PROGRESS-LOG.md、tasks/TASKS.md、self.opt）。
    - **Claude Code**：输入 `/` 查看所有可用命令
    - **Codex**：自动根据任务触发对应技能，或使用 `$skill-name` 手动触发
    - **Gemini CLI**：描述意图即可自动匹配技能
    - **Cursor**：规则自动生效，无需手动操作

**⚠️ Inspector CLI**（仅 **full-dev-脚手架-inspector** 或单独部署 sam-dev-cc-init 时可用）。在本仓库（Claude_skill_pool）中测试：
```bash
# 方式1: 相对路径 (在项目根目录)
bash skills.claude/sam-dev-cc-init/.claude/scripts/inspector-cli.sh dashboard

# 方式2: 部署到实际项目后
# 先将 package/full-dev-脚手架-inspector/ 或 skills.claude/sam-dev-cc-init/.claude/ 复制到目标项目根目录
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
    ├── skills/[skill]/          # 核心 SKILL.md + 支撑文件
    │   ├── SKILL.md
    │   ├── scripts/             # (可选) 脚本工具
    │   ├── references/          # (可选) 参考资料
    │   └── templates/           # (可选) 文档模板
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
            ├── agents/
            │   └── openai.yaml       # 接口配置（display_name / short_description / default_prompt）
            ├── scripts/              # (可选) 脚本工具
            ├── references/           # (可选) 参考资料
            └── templates/            # (可选) 文档模板
```

### Gemini CLI 技能结构

```text
skills.gemini/[skill-name]/
└── .gemini/
    └── skills/
        └── [skill-name]/
            ├── SKILL.md              # 核心 Skill 定义（含 YAML frontmatter）
            ├── scripts/              # (可选) 脚本工具
            ├── references/           # (可选) 参考资料
            └── templates/            # (可选) 文档模板
```

### Skill 元数据规范（SKILL.md frontmatter）

所有平台的 `SKILL.md` 统一使用 YAML frontmatter，便于发现与索引：

- **name**（必填）：小写字母与连字符，与目录名一致，如 `api-first-modular`、`code-debugger`。
- **description**（必填）：第三人称、一句话说明「做什么 + 何时使用」；可含触发场景关键词，便于 Agent 匹配。

示例：

```yaml
---
name: code-debugger
description: 基于深度上下文的智能代码调试与增量开发。用于 Bug 定位与修复、增量功能开发、技术栈 Checkfix 闭环及 .debug 文档维护。
---
```

目录命名与技能池保持一致：`skills.claude/`、`skills.codex/`、`skills.gemini/` 下均使用**英文小写+连字符**（如 `research-analyst-system`），避免中文或空格。

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
| **Superpowers (superpowers)** | `/superpowers` | `$superpowers` | ✓ | 泛用式 AI 任务处理框架；自动评估任务复杂度，按场景分流至 TDD 开发链、通用头脑风暴、任务拆解、信息收集或方案设计工作流，并内置 token 效率优化策略 |
| **PDCA 工作流初始化 (sam-dev-cc-init)** | `/sam-init` | — | — | 为项目一键初始化 CLAUDE.md、PROGRESS-LOG.md、tasks/TASKS.md、self.opt（项目级自优化） |
| **编程策略工具 (ai-spec)** | `/ai-spec` | `$ai-spec` | ✓ | 全栈架构师模式，将自然语言需求转化为生产级技术规范和 AI 执行指令 |
| **API-First 模块化 (api-first-modular)** | `/api-first` | `$api-first-modular` | ✓ | 后端功能封装为独立 API 包，前端只调 API，跨层任务按 API 边界自动分解 |
| **智能调试助手 (code-debugger)** | `/debug` | `$code-debugger` | ✓ | 基于深度上下文理解的精准调试与增量开发，模块隔离防止连锁错误 |
| **UI 设计师 (debug-ui)** | `/debug-ui` | `$debug-ui` | ✓ | 顶级 UI 设计师模式，六维视觉诊断 + 像素级代码实施，与 debug 共享 `.debug/` 文档 |
| **前端演示文稿 (frontend-slides)** | `/frontend-slides` | `$frontend-slides` | ✓ | 将内容或 PPT/PPTX 转换为高品质单文件 HTML 演示文稿；视口自适应、风格预设与交互动画，支持 extract-pptx.py 一键提取 |
| **PRD 生成器 (prd)** | `/prd` | — | ✓ | 交互式生成结构化产品需求文档 |
| **Ralph 工作流 (ralph)** | `/ralph` | `$ralph` | ✓ | 基于 PRD 的自主 Agent 循环，逐个实现 User Story 并自动提交 |
| **Ralph YOLO (ralph-yolo)** | `/ralph-yolo` | — | ✓ | Ralph 全自动模式，无人值守 |
| **Draw.io 路线图 (drawio-xml-roadmap)** | `/drawio-xml-roadmap` | `$drawio-xml-roadmap` | ✓ | 基于 draw.io XML 生成可导入的路线图/流程图，遵循 mxfile/mxCell 规范 |
| **ComfyUI 工作流 (comfyui-workflow-designer)** | `/comfyui-workflow` | `$comfyui-workflow-designer` | ✓ | 设计可导入 ComfyUI 的工作流 JSON（静图：FLUX.2/FLUX.1、SD3.5、Qwen-Image、Z-Image、SDXL 等；视频：Wan 等）；场景化架构选型、节点自检，CivitAI / HuggingFace / 官方示例检索 |
| **Inspector (PDCO 监管)** | — | `$inspector` | ✓ | 评估与管理所有 Agent 的质量、效率与成长（Codex/Gemini 版） |
| **Node.js npm 自动发版 (nodejs-npm-auto-release)** | ✓ | ✓ | ✓ | 标准化 npm 发版：自动版本号、GitHub Actions 发布与本地预检 |
| **Office 文档 (office-docs)** | `/office-docs` | `$office-docs` | ✓ | PPTX/DOCX/XLSX 读取、编辑、创建与校验，支持解包/打包 XML 与 PptxGenJS |
| **UX 体验审计 (ux-experience-audit)** | `/ux-experience-audit` | `$ux-experience-audit` | ✓ | 从用户体验角度做问题扫描、优先级判定与修复闭环，解决「功能可用但体验不通」 |

### 科研与文献

| 技能名称 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :--- |
| **Dr. Midas (dr-midas)** | `/midas` | `$dr-midas` | ✓ | 科研炼金术士，分析科研图表并结合 PubMed 文献生成深度科研叙事 |
| **PubMed Linker** | `/update-pubmed-links` | `$pubmed-linker` | ✓ | 自动查询并更新参考文献的 PubMed 链接、PMID、DOI |
| **论文投稿管理 (paper-submission-manager)** | `/paper-submission-manager` | `$paper-submission-manager` | ✓ | 论文投稿全流程管理：清单、QA、材料打包与提交追踪 |
| **SCI 期刊投稿专家 (sci-journal-submission-expert)** | `/sci-journal-submission-expert` | `$sci-journal-submission-expert` | ✓ | SCI 投稿预审与风险分级、梯度选刊、作者指南格式核查、数据与开放科学合规、审稿逐点回复框架、伦理与 APC 流程指引 |
| **单细胞细胞类型注释 (scrna-celltype-annotation)** | `/scrna-celltype-annotation` | `$scrna-celltype-annotation` | ✓ | 基于 Seurat 差异表达与文献 MCP 对单细胞亚群做 major/minor 注释并生成报告 |
| **识典古籍采集 (shidianguji-fetcher)** | `/shidianguji-fetcher` | `$shidianguji-fetcher` | ✓ | 从识典古籍 (shidianguji.com) 批量下载古籍文本，清洗后整理为结构化 Markdown 文件 |

### 研究与分析

| 技能名称 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :--- |
| **思路抽提 (extract)** | `/extract` | `$extract` | ✓ | 从深度研究文档中反向提取可复用的研究方法论框架和 Prompt 模板 |
| **金融分析师团队 (research-analyst-system)** | `/research` | `$research-analyst-system` | ✓ | 首席分析师 + 6 大研究小组并行深度调研，输出结构化投资报告 |

### 脚手架

| 名称 | 包含工具 | Claude | Codex | Gemini | 描述 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **企业咨询工具箱脚手架 (enterprise-use)** | Claude + Codex + Gemini | 6 commands<br>6+ skills | 6 skills | 6 skills | 面向企业咨询与文档协同：高管咨询、行政秘书、对外谈判、法律顾问、Office 文档处理、PDF 提取阅读；适合咨询团队或商务运营团队 |
| **全栈开发脚手架 (full-dev)** | Claude + Codex + Gemini + Cursor | 8 commands<br>9 skills | 7 skills | 9 skills | 仅开发能力：一键部署 ai-spec、api-first、debug、debug-ui、prd、ralph、ralph-yolo、ux-experience-audit、nodejs-npm-auto-release，**无** PDCA/Inspector |
| **全栈开发 + Inspector 脚手架 (full-dev-inspector)** | Claude + Codex + Gemini + Cursor | 9 commands<br>10 skills | 7 skills | 9 skills | 在 full-dev 基础上增加 **PDCA 工作流**：`/sam-init`、sam-dev-cc-init、PROGRESS-LOG、tasks、self.opt；适合需要入职看板与专家周期管理的项目，详见 [docs/inspector/](docs/inspector/) |

---

## 致谢

Inspector 相关设计与能力来源于 [@samqin123](https://github.com/samqin123) 的贡献，特此感谢。

[![@samqin123](https://github.com/samqin123.png?size=64)](https://github.com/samqin123)
