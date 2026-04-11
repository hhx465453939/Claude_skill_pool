---
name: shidianguji-fetcher
description: 从识典古籍 (shidianguji.com) 搜索古籍、批量下载章节并整理为 Markdown。用于古籍数字化采集、文本研究、语料整理等场景。
---

# 识典古籍采集助手（Gemini 版）

从「识典古籍」批量下载古籍文本，合并为 Markdown。与 Codex 源 `shidianguji-fetcher` 一致。

---

## 原理

章节页面 (`/book/XX/chapter/YY`) 服务端渲染，包含正文和全书章节列表。
给定任意章节 URL 即可发现并下载整本书。

---

## 使用

```bash
pip install -r scripts/requirements.txt
python scripts/fetch_book.py "<chapter_url>" --title 皇极经世
```

| 参数 | 说明 |
|------|------|
| `url` | 任意章节 URL（必填） |
| `--title` | 书名 |
| `--output` | 输出目录（默认 output） |
| `--delay` | 请求间隔秒（默认 1） |

---

## 文件

```
scripts/fetch_book.py      # 主脚本
scripts/requirements.txt   # 依赖
```

---

## Agent 流程

1. 用户给书名 → 在 shidianguji.com 搜索 → 找到章节 URL
2. 运行脚本 → 自动发现全部章节 → 下载 → Markdown
3. 输出 `output/{书名}_{时间戳}.md`
