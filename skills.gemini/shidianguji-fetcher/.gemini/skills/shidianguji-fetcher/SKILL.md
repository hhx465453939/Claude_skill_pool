---
name: shidianguji-fetcher
description: 识典古籍采集助手。用于从识典古籍网站（shidianguji.com）抓取古书章节内容，批量下载并合并为 Markdown。
homepage: https://www.shidianguji.com/
version: 0.1.0
---

# 识典古籍采集助手

**技能名称：** shidianguji-fetcher
**用途：** 从识典古籍 (shidianguji.com) 搜索书目、解析书籍/章节链接、检索已下载古籍上下文、导出单本 Markdown、批量打包 ZIP
**触发条件：** 用户提到「识典古籍」「古籍下载」「shidianguji」，或需要古籍原典、历史经典、古代政治语境、玄学典籍上下文时

---

## 核心原理

识典古籍网站的结构特点：

- **章节页面** (`/book/XX/chapter/YY`)：服务端渲染，包含完整正文 + 全书章节列表
- **书籍首页** (`/book/XX`)：SPA（单页应用），HTTP GET 拿不到数据
- **搜索功能** (`/search?q=...`)：目前不稳定，多数书籍搜索不到

**关键策略：**
> 拿到任意一个章节 URL，就能从该页面挖掘整本书的所有章节，然后逐章下载。

---

## 完整工作流

### 方案 A：使用搜索引擎找章节 URL（推荐）

**核心发现：识典古籍网站内部搜索功能失效，但通过外部搜索引擎可以找到！**

1. **使用搜索引擎查找**
   ```bash
   # 使用智谱搜索或其他搜索工具
   mcp_call zhipu-web-search-sse webSearchPro "书名 识典古籍"

   # 示例：搜韩非子
   mcp_call zhipu-web-search-sse webSearchPro "韩非子 识典古籍"
   ```

2. **从搜索结果中提取识典古籍链接**
   - 优先选择章节页面 URL：`https://www.shidianguji.com/book/{BOOK_ID}/chapter/{CHAPTER_ID}`
   - 如果找到的是书籍首页或 mid-page，尝试访问后从页面找章节链接

3. **运行 Node 命令**

```bash
node skills/shidianguji-fetcher/scripts/cli.js download "<chapter_url>" --title 书名
```

4. **脚本自动完成**
   - 从该章节页面挖掘所有章节链接
   - 逐章下载正文
   - 合并为 Markdown 文件

5. **输出结果**
   - 文件位置：`books/shidianguji-fetcher/{书名}_{bookId}.md`
   - 告知用户或读入上下文

---

### 方案 B：用户提供章节 URL（备用）

如果用户已经有识典古籍的章节 URL，可以直接使用：

1. **用户给出章节 URL**
   - 格式：`https://www.shidianguji.com/book/{BOOK_ID}/chapter/{CHAPTER_ID}`
   - 示例：`https://www.shidianguji.com/book/SBCK070/chapter/1j745z4cg5mbg_1`

2. **运行 Node 命令**

```bash
node skills/shidianguji-fetcher/scripts/cli.js download "<chapter_url>" --title 书名
```

3. **输出结果**
   - 文件位置：`books/shidianguji-fetcher/{书名}_{bookId}.md`
   - 告知用户或读入上下文

1. **用户给出章节 URL**
   - 格式：`https://www.shidianguji.com/book/{BOOK_ID}/chapter/{CHAPTER_ID}`
   - 示例：`https://www.shidianguji.com/book/SBCK070/chapter/1j745z4cg5mbg_1`

2. **运行 Node 命令**

```bash
node skills/shidianguji-fetcher/scripts/cli.js download "<chapter_url>" --title 书名
```

3. **脚本自动完成**
   - 从该章节页面挖掘所有章节链接
   - 逐章下载正文
   - 合并为 Markdown 文件

4. **输出结果**
   - 文件位置：`books/shidianguji-fetcher/{书名}_{bookId}.md`
   - 告知用户或读入上下文

---

### 方案 B：使用搜索工具（其他古籍网站）

对于**其他有正常搜索功能的古籍网站**，可以用搜索工具找到章节 URL：

1. **使用搜索工具**
   ```bash
   # 使用智谱搜索
   mcp_call zhipu-web-search-sse webSearchPro "书名 site:古籍网站域名"
   
   # 或使用 Tavily 搜索（如可用）
   mcp_call tavily-mcp-local tavily_search "书名 古籍网站"
   ```

2. **提取章节 URL**
   - 从搜索结果中找到章节页面链接
   - URL 必须包含 `/book/XXX/chapter/YYY` 格式

3. **执行方案 A 的步骤 2-4**

---

### 方案 C：识典古籍手动搜索（备用，不推荐）

识典古籍搜索功能不稳定，可手动搜索：

1. **用户手动搜索**
   - 访问 https://www.shidianguji.com/
   - 搜索书名
   - 点击任意章节
   - 复制章节 URL

2. **执行方案 B 的步骤 2-4**

**注意：** 识典古籍网站内部搜索功能经常失效（搜索结果为 0），推荐使用方案 A（外部搜索引擎）。

识典古籍搜索功能目前不稳定，可手动搜索：

1. **用户手动搜索**
   - 访问 https://www.shidianguji.com/
   - 搜索书名
   - 点击任意章节
   - 复制章节 URL

2. **执行方案 A 的步骤 2-4**

---

## CLI 参数

```bash
node skills/shidianguji-fetcher/scripts/cli.js <command> [options]
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `search <query>` | 搜索识典古籍书目 | ❌ |
| `context <query>` | 在本地已下载古籍中查找关键词上下文 | ❌ |
| `resolve <input>` | 解析书名 / bookId / 章节 URL 到可下载书籍 | ❌ |
| `download <input>` | 导出单本 Markdown | ❌ |
| `batch --input ...` | 批量打包多本书 | ❌ |
| `--title`, `-t` | 书名（覆盖自动推断标题） | ❌ |
| `--output-dir`, `-o` | 输出目录（默认 `workspace/books/shidianguji-fetcher`） | ❌ |
| `--max-chapters` | 仅抓前 N 章，便于 smoke/debug | ❌ |
| `--json` | 输出 JSON 结果 | ❌ |

---

## 示例

```bash
# 搜索《论语》
node skills/shidianguji-fetcher/scripts/cli.js search "论语"

# 在本地已下载古籍中查“变法”
node skills/shidianguji-fetcher/scripts/cli.js context "变法"

# 从章节 URL 下载《韩非子》
node skills/shidianguji-fetcher/scripts/cli.js download "https://www.shidianguji.com/book/SBCK070/chapter/1j745z4cg5mbg_1" --title 韩非子

# 直接从书名下载《皇极经世》
node skills/shidianguji-fetcher/scripts/cli.js download "皇极经世" --max-chapters 3

# 批量打包
node skills/shidianguji-fetcher/scripts/cli.js batch --input "论语" --input "皇极经世"
```

---

## 当前运行方式

- **不再走 Python `.venv`**
- **不在 skill 调用时 `npm install`**
- 直接使用 openclaw 容器里已存在的 Node runtime 与 repo 依赖
- 解析与打包逻辑已切换到 Node 脚本
- 网络层显式支持容器内 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY`，并带重试、超时、退避

## 当前限制

- **识典古籍搜索功能不稳定**：多数经典古籍（如《论语》《鬼谷子》《孙子兵法》等）搜索不到
- **无浏览器会话兜底**：当前保持轻量 HTTP 抓取，不引入 Playwright
- **仅限识典古籍网站**：脚本专门针对该网站结构设计，其他网站需要调整

---

## Guardrails

- ✅ 仅限学术用途
- ⏱️ 请求间隔使用轻量节流（默认 120ms），并带失败重试与退避
- 📄 尊重版权，下载内容仅供个人学习研究

---

## 已知可用书籍

通过搜索引擎测试（2026-03-26），以下书籍在识典古籍上有链接：

| 书籍 | 是否有识典古籍链接 | 链接类型 | 验证状态 |
|------|-------------------|---------|----------|
| 《韩非子》 | ✅ 有 | 章节 URL | 已验证（SBCK070, DZ1177 两个版本） |
| 《论语》 | ✅ 有 | mid-page | 已验证 |
| 《鬼谷子》 | ❌ 无 | - | 搜索未找到 |
| 《孙子兵法》 | ❌ 无 | - | 搜索未找到 |
| 《资治通鉴》 | ❌ 无 | - | 搜索未找到 |
| 《战国策》 | ❓ 未知 | - | 未测试 |

**说明：**
- "有章节 URL"：可以直接用于下载脚本
- "有 mid-page"：可能需要进一步处理才能用于下载
- "无"：识典古籍数据库中可能没有这本书，或者搜索引擎索引不全

---

## 文件结构

```
shidianguji-fetcher/
├── scripts/
│   ├── cli.js                # Node CLI：search / resolve / download / batch
│   └── runtime-lib.js        # 轻量 runtime：搜索、抓取、Markdown、ZIP
├── .claude/
│   ├── commands/
│   │   └── shidianguji-fetcher.md
│   └── skills/
│       └── shidianguji-fetcher.md
└── SKILL.md
```

---

## 更新日志

- 2026-03-26：发现外部搜索引擎可以绕过识典古籍内部搜索限制
  - 更新工作流：方案 A 改为"使用搜索引擎查找"
  - 验证了 6 本古籍的可用性：韩非子✅、论语✅、鬼谷子❌、孙子兵法❌、资治通鉴❌、战国策❓
  - 识典古籍内部搜索功能失效，但外部搜索引擎（如智谱搜索）可以找到识典古籍的链接
- 2026-03-26：初始版本，记录搜索功能限制和工作流程
