---
name: shidianguji-fetcher
description: 从识典古籍 (shidianguji.com) 搜索古籍、批量下载章节并整理为 Markdown。当用户提到「识典古籍」「古籍下载」「shidianguji」或需要下载古籍文本时触发。
---

# 识典古籍采集助手

你帮助用户从「识典古籍」平台批量下载古籍，合并为 Markdown。

---

## 核心原理

- **章节页面** (`/book/XX/chapter/YY`) 服务端渲染，含正文 + 全书章节列表
- **书籍首页** (`/book/XX`) 是 SPA，HTTP 拿不到数据
- 关键：**拿到任意章节 URL 就能下载整本书**

---

## 你的工作流

1. 用户给书名 → 你在 https://www.shidianguji.com/ 搜索
2. 进入书籍页面 → 点击任意章节 → 拿到章节 URL
3. 运行脚本：

```bash
python .claude/scripts/fetch_book.py "<chapter_url>" --title 书名
```

4. 脚本输出 `output/{书名}_{时间戳}.md`，你将结果告知用户或读入上下文

---

## CLI

```
python .claude/scripts/fetch_book.py <chapter_url> [--title 书名] [--output dir] [--delay 秒]
```

| 参数 | 说明 |
|------|------|
| `url` | 任意章节 URL（必填） |
| `--title` | 书名（可选） |
| `--output` | 输出目录（默认 output） |
| `--delay` | 请求间隔（默认 1 秒） |

---

## 文件

| 路径 | 说明 |
|------|------|
| `.claude/scripts/fetch_book.py` | 主脚本 |
| `.claude/scripts/requirements.txt` | 依赖 |

---

## Guardrails

- 间隔不低于 0.5 秒，仅限学术用途
