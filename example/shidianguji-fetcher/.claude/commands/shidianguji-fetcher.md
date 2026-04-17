---
description: 从识典古籍下载古籍并整理为 Markdown
---

# /shidianguji-fetcher

从识典古籍 (shidianguji.com) 搜索古籍、导出单本 Markdown，或批量打包为 ZIP。

```
/shidianguji-fetcher 皇极经世
/shidianguji-fetcher https://www.shidianguji.com/book/DZ1040/chapter/1k1r7oqmxaxaz
/shidianguji-fetcher batch 论语 皇极经世
```

默认改走 Node CLI：

```bash
node skills/shidianguji-fetcher/scripts/cli.js download "<input>"
```

如果用户明确要批量：

```bash
node skills/shidianguji-fetcher/scripts/cli.js batch --input "论语" --input "皇极经世"
```

详见：`.claude/skills/shidianguji-fetcher.md`
