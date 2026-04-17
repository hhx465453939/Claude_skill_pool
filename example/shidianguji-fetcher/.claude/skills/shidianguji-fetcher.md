---
name: shidianguji-fetcher
description: 从识典古籍 (shidianguji.com) 搜索古籍、解析书籍/章节链接、导出 Markdown，并批量打包 ZIP。当用户提到「识典古籍」「古籍下载」「shidianguji」或需要下载古籍文本时触发。
---

# 识典古籍采集助手

你帮助用户从「识典古籍」平台搜索书目、解析入口、导出 Markdown，以及批量打包下载。

---

## 核心原理

- **章节页面** (`/book/XX/chapter/YY`) 服务端渲染，含正文 + 全书章节列表
- **书籍首页** (`/book/XX`) 是 SPA，HTTP 拿不到数据
- 关键：**拿到任意章节 URL 就能下载整本书**

---

## 你的工作流

1. 用户给书名 / bookId / 链接
2. 优先运行 Node CLI，而不是 Python 脚本
3. 常用命令：

```bash
node skills/shidianguji-fetcher/scripts/cli.js search "论语"
node skills/shidianguji-fetcher/scripts/cli.js resolve "https://www.shidianguji.com/book/DZ1040"
node skills/shidianguji-fetcher/scripts/cli.js download "皇极经世"
node skills/shidianguji-fetcher/scripts/cli.js batch --input "论语" --input "皇极经世"
```

4. 脚本输出 `FILEPATH:...` 时，直接把文件路径回给用户或继续后续交付

---

## CLI

`download` / `batch` 不应触发 `npm install` 或 Python `.venv` 创建。当前设计默认复用 openclaw 容器内已有 Node runtime，并显式支持代理环境变量与失败重试。

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
| `scripts/cli.js` | 当前主入口 |
| `scripts/runtime-lib.js` | 搜索/解析/导出/打包逻辑 |

---

## Guardrails

- 默认轻量节流 120ms，仅限学术用途
- 不要在 skill 调用阶段执行 `npm install`
- 不要在 skill 调用阶段创建 Python `.venv`
