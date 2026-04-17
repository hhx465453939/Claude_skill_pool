# AGENTS.md - enterprise use

该脚手架为 Codex 提供 7 个技能（显式调用使用 `$skill-name`）：

- `$executive-consultant` — 高管咨询 / 参谋长增强
- `$executive-secretary` — 高级行政秘书（可联动高德地图 MCP）
- `$external-negotiation-master` — 对外谈判大师 / 超级说客
- `$global-legal-counsel` — 全球法律顾问 / 总法律顾问
- `$office-docs` — PPTX / DOCX / XLSX 读写编辑与校验
- `$pdf-reader` — 本地 PDF → Markdown 提取
- `$deep-research` — 多 Agent 并行深度调研（引用管理、量化验证、稳定交付）

## 使用方式

1. 将本脚手架 `.codex/` 合并到目标项目根目录。
2. Codex 会根据任务描述自动匹配对应技能；也可用 `$skill-name` 手动触发。
3. 每个技能均带有 `agents/openai.yaml`（含 `display_name` / `short_description` / `default_prompt`）。

更多细节见 `README.md`。
