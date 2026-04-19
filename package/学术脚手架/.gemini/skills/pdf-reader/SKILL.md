---
name: pdf-reader
description: 用 pdfplumber 快速提取本地 PDF 的纯文本并转成 Markdown，便于后续阅读、总结和分析。适用于用户发来的 PDF，或从 OpenAlex、PubMed、网页抓取后落到本地的 PDF 文件。仅覆盖有文本层的 PDF；扫描件/图片型 PDF 会明确提示无法直接提取。
---

# PDF Reader

用这个 skill 处理“先把本地 PDF 变成可读文本，再继续分析”的场景。

## 适用范围

- 用户给了一个本地 `.pdf` 文件路径
- PDF 是从 OpenAlex、PubMed 或网页下载到本地的
- 目标是快速阅读、摘要、问答、提炼要点

## 不做的事

- 不做 OCR
- 不处理扫描版/纯图片 PDF
- 不保证表格、双栏排版、脚注完全还原

如果脚本提示“没有可提取文本”，直接告诉用户这份 PDF 很可能是扫描件，需要 OCR 流程；不要在这个 skill 里继续硬拆。

## 快速使用

默认把 Markdown 写到 PDF 同目录下的同名 `.md` 文件：

```bash
uv run --with pdfplumber python3 workspace/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf
```

显式指定输出文件：

```bash
uv run --with pdfplumber python3 workspace/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --output /path/to/file.md
```

只抽取部分页码：

```bash
uv run --with pdfplumber python3 workspace/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --first-page 1 --last-page 5
```

直接打印到标准输出：

```bash
uv run --with pdfplumber python3 workspace/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --stdout
```

## 推荐工作流

1. 先运行脚本，把 PDF 转成 Markdown。
2. 再读取生成的 Markdown，而不是反复对原 PDF 做低效猜测。
3. 对长文档先抽前几页确认质量；质量正常后再跑全文。
4. 如果输出字符极少或大量空页，视为“无文本层 PDF”，直接告知限制。

## 输出约定

- 顶部写入源文件路径和页码范围
- 每页用 `## Page N` 分段
- 保留空页提示，避免页码错位

## 相关说明

- 在当前 workspace runtime 里，本地 `.pdf` 被 `read` 工具读取时，会自动改走缓存的 Markdown sidecar（`*.pdf.md`）。
- 入站文件型 PDF 是否会自动进入上下文，取决于 channel 是否正确提供 `MediaPath/MediaType` 并走通用 file preprocessing；这个不由本 skill 单独保证。
- 这个 skill 只负责 PDF 文本提取与阅读前处理。
- 如果用户要处理 `docx`，改用 `office-docs` 或专门的 DOCX skill。
