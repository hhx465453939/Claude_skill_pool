---
name: pubmed-linker
description: PubMed 文献链接查询与更新技能。系统化查询参考文献的 PubMed 链接、PMID、DOI，批量更新 Reference_list.md，检测开放获取状态并下载全文。需配合 MCP PubMed 工具。
---

# PubMed Linker - 文献链接查询与更新

## Overview

系统化使用 MCP PubMed 工具查询文献信息并更新参考文献列表的链接，支持批量处理和全文下载检测。

## Available MCP Tools

- `pubmed_search` / `pubmed_quick_search` — 搜索文献
- `pubmed_get_details` / `pubmed_batch_query` — 获取详细信息
- `pubmed_extract_key_info` — 提取关键摘要
- `pubmed_download_fulltext` / `pubmed_batch_download` — 下载全文 PDF
- `pubmed_detect_fulltext` — 检测开放获取状态
- `pubmed_cross_reference` — 查找相关文献

## Workflow

### 1. 解析引用

从 `Reference_list.md` 提取：第一作者姓氏、题目关键词(2-3个)、期刊名、发表年份。

### 2. 优先级搜索策略

**策略 1**：`作者姓氏 AND 关键词1 AND 关键词2`
**策略 2**：`期刊名[ta] AND 年份[dp] AND 关键词`
**策略 3**：完整题目精确匹配

### 3. 验证匹配

匹配成功需满足：PMID 存在、作者匹配、题目相似度 >80%、年份一致、期刊匹配。

### 4. 更新文档

在原始引用后添加：
```markdown
- **PMID**: {PMID}
- **PubMed**: https://pubmed.ncbi.nlm.nih.gov/{PMID}/
- **DOI**: https://doi.org/{DOI}
- **Fulltext**: {下载链接或状态}
```

### 5. 批量处理

- 每次处理 5-10 篇，避免超时。
- 优先使用 `pubmed_batch_query`。
- 维护处理进度，支持断点续传。

## Error Handling

- 未找到 → 尝试不同策略 → 标注 `⚠️ 未找到匹配`
- 多个匹配 → 选最佳 → 若有歧义标注 `⚠️ 需人工确认`
- 全文不可获取 → 检测开放获取 → 标注 `🔒 订阅限制`

## Guardrails

- 精确性优先：多条件交叉验证。
- 保留原始引用格式不修改。
- 对无法确认的信息明确标注。
- PubMed 数据库有延迟，最新文献可能未收录。
- 非 PubMed 收录文献需手动处理。
