# CLAUDE.md - 学术脚手架

本脚手架为 Claude Code 提供与学术、科研、文献、医学与古籍相关的 **slash commands**（见 `.claude/commands/`），核心逻辑在 `.claude/skills/` 与各技能子目录中。

## 技能命令一览（与 `.claude/commands/*.md` 文件名一致）

- `/paper-reader` — 论文精读
- `/paper-submission-manager` — 投稿管理
- `/sci-journal-submission-expert` — SCI 期刊专家
- `/nsfc-proposal-advisor` — 国自然辅导
- `/thesis-writing-mentor` — 学位论文顾问
- `/deep-research` — 深度调研编排
- `/pdf-reader` — PDF 转 Markdown
- `/extract` — 研究方法论抽提（技能正文见 `skills/extract-research-framework.md`）
- `/midas` — Dr. Midas：科研图表 + PubMed 叙事（对应 `dr-midas` 技能包）
- `/scrna-celltype-annotation` — 单细胞注释
- `/medical-advisory` — 循证 + 中医顾问
- `/shidianguji-fetcher` — 识典古籍采集
- `/update-pubmed-links` — PubMed 链接 / PMID / DOI 批量更新（配套 `skills/pubmed-linker/`）

详细说明与部署见 `README.md`。
