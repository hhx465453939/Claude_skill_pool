# Inspector 文档

本目录为 **Inspector Agent（PDCO 全局监管系统）** 的说明与场景文档，供理解设计、各平台实现与使用流程。这些文档**不参与**脚手架或脚本执行，仅作阅读与参考。

| 文档 | 说明 |
|------|------|
| [INSPECTOR-CROSS-PLATFORM.md](./INSPECTOR-CROSS-PLATFORM.md) | 跨平台架构与实现：Claude / Codex / Gemini / Cursor 的 Inspector 位置、CLI 用法、统一标准与故障排查 |
| [INSPECTOR-SCENARIO-WALKTHROUGH.md](./INSPECTOR-SCENARIO-WALKTHROUGH.md) | 场景演示：从 Backend Agent 入职到专家的完整周期（PLAN/DO/CHECK/OPT、等级与 self-opt 演化） |

实际可执行能力来自各技能包与脚本，例如：

- **Claude**：`skills.claude/sam-dev-cc-init/.claude/`（含 `inspector-agent.md`、`inspector-cli.sh`）
- **Codex**：`skills.codex/inspector/`
- **Gemini**：`skills.gemini/inspector/`
