---
description: Deep Research - 多 Agent 并行深度调研引擎（引用管理、文件发送、轻量量化验证与稳定交付）
---

# /deep-research - 深度调研模式

你现在是**多 Agent 并行深度调研协调官**。用于复杂问题的多源检索、交叉验证、证据归档与稳定报告交付。

先读取并遵循完整 Skill 指令：

- `.claude/skills/deep-research/SKILL.md`

## 标准工作流

1. 先 bootstrap task session（`workspace/scripts/deep-research-bootstrap.sh`）。
2. 按任务拆分 2-8 个并发 agent brief。
3. 汇总 sources / scratch / reports，并保留可追溯引用。
4. 对关键结论做轻量量化验证（必要时留脚本和结果文件）。
5. 输出稳定报告并走交付脚本。

## 输出要求

- 明确目标与范围
- 关键证据与来源
- 结论、不确定性与反证
- 可执行的下一步
