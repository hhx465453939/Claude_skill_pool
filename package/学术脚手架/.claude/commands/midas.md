---
description: 启动 Dr. Midas 科研炼金术士，分析图表并生成深度科研叙事
---

# Dr. Midas (科研炼金术士)

启动 Dr. Midas 角色，帮助你分析科研数据（图片/图表），结合 PubMed 文献检索，将平淡的数据转化为引人入胜的科学故事。

## 使用前提
1.  **必须上传图片**: 请在对话中直接粘贴或上传你的科研结果图（Western Blot, 统计图, 热图, 流式图等）。
2.  **MCP 工具依赖**: 本技能高度依赖 `pubmed-mcp` 和 `metaso-search` (或类似的搜索工具)。请确保你的 Claude Code 环境已配置相应的 MCP Server。
    - 必需工具: `pubmed_search`, `pubmed_extract_key_info`, `metaso_search` 等。

## 使用方法

1.  上传图片。
2.  输入 `/midas` 启动分析。
3.  Dr. Midas 将会自动执行：视觉解码 -> 文献验证 -> 叙事重构。

## 示例
> (上传一张生存曲线图)
> /midas 分析这张图，重点关注与免疫治疗响应的关系
