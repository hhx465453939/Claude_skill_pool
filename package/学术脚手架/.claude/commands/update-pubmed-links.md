---
description: 更新 Reference_list.md 中文献的 PubMed 链接和下载链接
argument-hint: [start] [end] [--force]
allowed-tools: [Read, Edit, Write, Glob, mcp__pubmed-data-server__pubmed_search, mcp__pubmed-data-server__pubmed_quick_search, mcp__pubmed-data-server__pubmed_get_details, mcp__pubmed-data-server__pubmed_batch_query, mcp__pubmed-data-server__pubmed_detect_fulltext, mcp__pubmed-data-server__pubmed_download_fulltext, mcp__pubmed-data-server__pubmed_cache_info]
---

# 更新 PubMed 文献链接

这个命令用于查询和更新 `Reference_list.md` 中文献的 PubMed 链接、DOI 和全文下载链接。

## 参数说明

- `$ARGUMENTS` - 可选参数
  - `start` - 起始文献序号（默认从 1 开始）
  - `end` - 结束文献序号（默认到最后一篇）
  - `--force` - 强制重新查询已更新的文献

## 执行步骤

### 1. 环境检查
首先使用 `pubmed_system_check` 验证 MCP 工具可用性。

### 2. 读取文献列表
使用 `Read` 工具读取 `Reference_list.md`，解析所有文献引用。

### 3. 解析文献信息
对每篇文献提取：
- 序号
- 第一作者姓氏
- 题目关键词（2-3个核心词）
- 期刊名
- 发表年份

### 4. 查询 PubMed
使用以下搜索策略（按优先级）：

**策略 A**: 作者姓氏 + 题目关键词
```python
pubmed_search(
    query=f"{first_author} AND {keyword1} AND {keyword2}",
    max_results=5
)
```

**策略 B**: 期刊名 + 年份 + 关键词
```python
pubmed_search(
    query=f"{journal}[ta] AND {year}[dp] AND {keyword}",
    max_results=5
)
```

### 5. 验证匹配结果
检查返回结果是否匹配：
- PMID 存在
- 作者姓名匹配
- 题目相似度 >80%
- 年份一致
- 期刊名匹配

### 6. 获取详细信息
对匹配的文献使用 `pubmed_get_details` 获取：
- PMID
- DOI
- 全文链接
- 开放获取状态

### 7. 检测全文可用性
使用 `pubmed_detect_fulltext` 检查是否可下载全文。

### 8. 更新文档
在原始引用后添加链接信息：

```markdown
[序号] 作者. 题目[J]. 期刊名, 年份, 卷(期): 页码.
- **PMID**: {PMID}
- **PubMed**: https://pubmed.ncbi.nlm.nih.gov/{PMID}/
- **DOI**: https://doi.org/{DOI}
- **Fulltext**: {状态/链接}
```

### 9. 批量处理优化
- 每处理 5 篇文献后报告进度
- 使用 `pubmed_cache_info` 检查缓存状态
- 如遇连续失败，暂停并询问是否继续

### 10. 完成报告
输出处理结果摘要：
- 总处理文献数
- 成功更新数
- 未找到匹配数
- 需要人工确认数

## 使用示例

```
/update-pubmed-links              # 处理所有文献
/update-pubmed-links 1 10         # 只处理文献 1-10
/update-pubmed-links 50 100       # 处理文献 50-100
/update-pubmed-links --force      # 强制重新查询所有文献
```

## 注意事项

1. **不修改原始引用** - 仅在引用后添加链接信息
2. **标注不确定项** - 对无法确认的匹配添加 `⚠️` 标记
3. **合理超时** - 单次查询超时 30 秒
4. **保持原格式** - 维持 markdown 格式一致性
