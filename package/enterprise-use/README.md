# Enterprise Use Scaffold

企业咨询工具箱脚手架（enterprise use），面向企业咨询、管理决策、谈判推进、法务研判、Office/PDF 文档处理与深度调研协作场景。一次部署即可让 Claude Code、Codex、Gemini CLI 三端共享同一套业务技能。

## 包含技能（7 个）

| 技能 | 定位 | Claude | Codex | Gemini |
|------|------|--------|-------|--------|
| **executive-consultant** | 高管咨询 / 参谋长增强 | `/executive-consultant` | `$executive-consultant` | ✓ |
| **executive-secretary** | 高级行政秘书 + 高德地图 MCP | `/executive-secretary` | `$executive-secretary` | ✓ |
| **external-negotiation-master** | 对外谈判大师 / 超级说客 | `/external-negotiation-master` | `$external-negotiation-master` | ✓ |
| **global-legal-counsel** | 全球法律顾问 / 总法律顾问 | `/global-legal-counsel` | `$global-legal-counsel` | ✓ |
| **office-docs** | PPTX / DOCX / XLSX 读写编辑与校验 | `/office-docs` | `$office-docs` | ✓ |
| **pdf-reader** | 本地 PDF → Markdown 提取阅读前处理 | `/pdf-reader` | `$pdf-reader` | ✓ |
| **deep-research** | 多 Agent 并行深度调研（引用管理、量化验证、稳定交付） | `/deep-research` | `$deep-research` | ✓ |

## 目录结构

```
package/enterprise-use/
├── CLAUDE.md         # Claude Code 入口说明
├── AGENTS.md         # Codex 入口说明
├── GEMINI.md         # Gemini CLI 入口说明
├── README.md
├── .claude/          # Claude Code：7 commands + 7 skills（含 office-docs 脚本工具链）
│   ├── commands/
│   ├── skills/
│   └── scripts/      # office-docs 的 Python 脚本工具链
├── .codex/           # Codex：7 skills（含 SKILL.md + agents/openai.yaml + 脚本/参考资料）
│   └── skills/
└── .gemini/          # Gemini CLI：7 skills
    └── skills/
```

## 适用团队

- 咨询公司 / 管理咨询团队
- 战略发展 / 投融资 / 法务 / BD / 行政秘书
- 需要配套文档（PPTX/DOCX/XLSX、PDF）和深度调研的业务运营团队
- 任何希望在 Claude Code、Codex、Gemini CLI 三端共享同一套企业咨询能力的项目

## 一键部署

### 方法一：完全替换（推荐新项目）

```bash
cp -r package/enterprise-use/*       /path/to/your-project/
cp -r package/enterprise-use/.[a-z]* /path/to/your-project/
```

### 方法二：增量合并（推荐有存量代码的项目）

```bash
# 复制入口文档
cp package/enterprise-use/{CLAUDE,AGENTS,GEMINI}.md /path/to/your-project/

# 合并 Claude Code
mkdir -p /path/to/your-project/.claude
cp -r package/enterprise-use/.claude/* /path/to/your-project/.claude/

# 合并 Codex
mkdir -p /path/to/your-project/.codex
cp -r package/enterprise-use/.codex/* /path/to/your-project/.codex/

# 合并 Gemini CLI
mkdir -p /path/to/your-project/.gemini
cp -r package/enterprise-use/.gemini/* /path/to/your-project/.gemini/
```

## 快速使用

- **Claude Code**：重启会话后输入 `/` 即可看到 7 个命令；典型组合：
  - `/executive-consultant` → 高管诊断 + 参谋长增强
  - `/global-legal-counsel` → 法律框架 + 风险矩阵
  - `/external-negotiation-master` → 谈判打法 + 可直接发送的话术
  - `/deep-research` → 复杂议题做多 Agent 深度调研并出报告
  - `/office-docs` / `/pdf-reader` → 承接交付文档与原始资料
- **Codex**：自动按任务匹配，或使用 `$skill-name` 手动触发。
- **Gemini CLI**：描述意图后 CLI 会自动匹配对应技能。

## 建议协作流

1. **立项阶段**：`/executive-consultant` 做战略与组织诊断；必要时 `/deep-research` 补事实基线与证据。
2. **执行阶段**：`/external-negotiation-master` 规划对外沟通与话术；`/executive-secretary` 安排多地日程与通勤。
3. **风险阶段**：`/global-legal-counsel` 做合规与诉讼推演；必要时再次 `/deep-research` 追踪法规或监管最新口径。
4. **交付阶段**：`/office-docs` 产出 PPTX / DOCX / XLSX；`/pdf-reader` 将来方 PDF 转 Markdown 后再喂给其他技能。

## 版本说明

- 本脚手架来源：`skills.codex/`、`skills.claude/`、`skills.gemini/` 三端标准库中对应技能的最新版本。
- 每次这 7 个技能在标准库内升级后，可再次运行分发流程把 `package/enterprise-use` 刷新到最新。
