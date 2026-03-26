---
name: shidianguji-fetcher
description: 从识典古籍网站 (shidianguji.com) 搜索古籍、批量下载章节并整理为 Markdown。用于古籍数字化采集、文本研究、语料整理等场景。
---

# 识典古籍采集助手

从「识典古籍」(https://www.shidianguji.com/) 批量下载古籍文本，合并为结构化 Markdown。

---

## 核心原理

识典古籍是 SPA 网站：
- **书籍首页** (`/book/XX`) 是客户端渲染，HTTP GET 拿不到章节列表
- **章节页面** (`/book/XX/chapter/YY`) 是服务端渲染，包含完整正文 + 全部章节链接

因此：**只要拿到任意一个章节 URL，就能发现并下载整本书**。

---

## Agent Workflow

### Step 1：用户给出书名

用户说：「帮我下载《皇极经世》」

### Step 2：Agent 搜索章节 URL

Agent 在 https://www.shidianguji.com/ 搜索书名，进入书籍页面，点击任意章节，获得一个章节 URL：

```
https://www.shidianguji.com/book/DZ1040/chapter/1k1r7oqmxaxaz
```

> 章节 URL 特征：路径包含 `/book/{BOOK_ID}/chapter/{CHAPTER_ID}`

### Step 3：运行脚本

```bash
pip install -r scripts/requirements.txt  # 仅首次
python scripts/fetch_book.py "<chapter_url>" --title 皇极经世
```

### Step 4：获取结果

脚本自动完成：章节发现 → 逐章下载 → Markdown 合并。
输出文件：`output/{书名}_{时间戳}.md`

---

## CLI 参数

```
python scripts/fetch_book.py <chapter_url> [options]
```

| 参数 | 必填 | 默认 | 说明 |
|------|:----:|------|------|
| `url` | 是 | — | 任意章节 URL |
| `--title / -t` | 否 | book_id | 书名 |
| `--output / -o` | 否 | `output` | 输出目录 |
| `--delay / -d` | 否 | `1.0` | 请求间隔秒数 |

---

## Scripts

| 文件 | 说明 |
|------|------|
| `scripts/fetch_book.py` | 主脚本（~140 行） |
| `scripts/requirements.txt` | 依赖：requests, beautifulsoup4, lxml |

---

## Output

```markdown
# {书名}
**来源:** https://www.shidianguji.com/
**时间:** 2026-03-26 15:50:46
---
## 目录
1. [章节标题](#anchor) ...
---
## 1. 章节标题
**来源:** https://www.shidianguji.com/book/.../chapter/...
---
（正文）
```

---

## Guardrails

- 默认 1 秒请求间隔，勿低于 0.5 秒
- 仅限学术研究和个人学习
- 输出仅保存在本地
