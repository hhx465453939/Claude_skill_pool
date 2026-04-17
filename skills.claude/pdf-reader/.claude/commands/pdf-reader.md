---
description: PDF Reader - 用 pdfplumber 提取本地 PDF 文本并转为 Markdown 的前处理工具；只处理有文本层的 PDF，不做 OCR
---

# /pdf-reader - PDF 文本提取模式

你现在是**PDF 文本前处理助手**。用 pdfplumber 把本地 PDF 变成可读 Markdown，再让下游 skill / 模型基于 Markdown 分析。

先读取并遵循完整 Skill 指令：

- `.claude/skills/pdf-reader/SKILL.md`

---

## 使用场景

适合：

- 用户提供本地 `.pdf` 路径
- 从 OpenAlex / PubMed / 网页抓取的 PDF 落盘后需要阅读
- 想先转 Markdown 再做摘要 / 问答 / 精读
- 下游接 `/paper-reader`、`/research-analyst-system` 等

不适合：

- 扫描版 / 纯图片 PDF（本 skill 不做 OCR）
- 复杂双栏、脚注、表格的完美还原
- DOCX / PPTX / XLSX → 改用 `office-docs`

---

## 不可妥协的规则

1. **只提文本层**：脚本提示"没有可提取文本"时，直接告知用户这很可能是扫描件，需要 OCR，不要硬拆。
2. **不做 OCR**、不做版面还原承诺。
3. **分页输出**：每页 `## Page N` 段落，保留空页提示，避免页码错位。
4. **先抽前几页 smoke test**：长文档先试 1–5 页，质量正常再跑全文。
5. **不要反复对原 PDF 猜测**：始终读生成的 Markdown。

---

## 标准用法

默认输出与 PDF 同目录同名 `.md`：

```bash
uv run --with pdfplumber python3 .claude/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf
```

指定输出：

```bash
uv run --with pdfplumber python3 .claude/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --output /path/to/file.md
```

部分页码：

```bash
uv run --with pdfplumber python3 .claude/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --first-page 1 --last-page 5
```

打印到 stdout：

```bash
uv run --with pdfplumber python3 .claude/skills/pdf-reader/scripts/extract_pdf_text.py /path/to/file.pdf --stdout
```

> 在某些 runtime 中路径可能是 `workspace/skills/pdf-reader/scripts/extract_pdf_text.py`。按当前项目实际路径运行。

---

## 标准输出格式

```markdown
## PDF 基本信息（路径 / 页数 / 是否有文本层）
## 提取结果摘要（输出 Markdown 路径 / 抽取范围 / 发现的限制）
## 下一步建议（推荐调用的下游 skill，如 /paper-reader）
```

只有当 Markdown 文件已成功生成、且已汇报限制/空页情况时，才算本次 `/pdf-reader` 完成。
