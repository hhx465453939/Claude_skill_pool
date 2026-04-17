# CLAUDE.md - enterprise use

该脚手架为企业咨询场景提供 7 个 Claude 命令：

- `/executive-consultant` — 高管咨询 / 参谋长增强
- `/executive-secretary` — 高级行政秘书（可联动高德地图 MCP）
- `/external-negotiation-master` — 对外谈判大师 / 超级说客
- `/global-legal-counsel` — 全球法律顾问 / 总法律顾问
- `/office-docs` — PPTX / DOCX / XLSX 读写编辑与校验
- `/pdf-reader` — 本地 PDF → Markdown 提取
- `/deep-research` — 多 Agent 并行深度调研（引用管理、量化验证、稳定交付）

## 使用方式

1. 将本脚手架 `.claude/` 合并到目标项目根目录。
2. 重启 Claude Code 会话。
3. 输入 `/` 查看全部命令；在需要时触发对应命令。
4. 典型组合链路：
   - 先 `/executive-consultant` 诊断 → 再 `/external-negotiation-master` 设计话术 → 必要时 `/global-legal-counsel` 做风险审视 → 复杂议题上 `/deep-research` → 最终由 `/office-docs` 落到正式交付物。

详细说明与目录结构见 `README.md`。
