---
description: 从识典古籍下载古籍并整理为 Markdown
---

# /shidianguji-fetcher

从识典古籍 (shidianguji.com) 批量下载古籍，合并为 Markdown。

```
/shidianguji-fetcher 皇极经世
/shidianguji-fetcher https://www.shidianguji.com/book/DZ1040/chapter/1k1r7oqmxaxaz
```

收到书名时：先在网站搜索找到章节 URL，再运行 `.claude/scripts/fetch_book.py`。
收到章节 URL 时：直接运行脚本。

详见：`.claude/skills/shidianguji-fetcher.md`
