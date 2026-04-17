# GEMINI.md - enterprise use

该脚手架为 Gemini CLI 提供 7 个技能：

- executive-consultant — 高管咨询 / 参谋长增强
- executive-secretary — 高级行政秘书（可联动高德地图 MCP）
- external-negotiation-master — 对外谈判大师 / 超级说客
- global-legal-counsel — 全球法律顾问 / 总法律顾问
- office-docs — PPTX / DOCX / XLSX 读写编辑与校验
- pdf-reader — 本地 PDF → Markdown 提取
- deep-research — 多 Agent 并行深度调研（引用管理、量化验证、稳定交付）

## 使用方式

1. 将本脚手架 `.gemini/` 合并到目标项目根目录（或用户级 `~/.gemini/` / `~/.agents/`）。
2. 描述你的任务即可；Gemini CLI 会根据 `SKILL.md` 中的 `description` 自动匹配激活。
3. 激活后 Gemini 会加载完整 SKILL.md 与其下的 `references/`、`scripts/` 资源。

更多细节见 `README.md`。
