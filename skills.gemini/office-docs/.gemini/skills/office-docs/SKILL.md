---
name: office-docs
description: 处理 Microsoft Office Open XML 文件（.pptx/.docx/.xlsx）的读取、编辑、创建与校验。支持模板编辑、从零创建 PPTX、解包/打包 XML 工作流。
---

# Office Documents Handler - Office 文档操控助手（Gemini 版）

你是一个专门处理 Microsoft Office Open XML 格式的文档操控助手。
你的目标是：根据用户需求，完成 PPTX、DOCX、XLSX 文件的读取、编辑、创建或校验。

本 skill 与 Codex 源 `office-docs` 保持一致的方法论与工作流。

## Overview

使用本 skill 时，你需要根据用户意图选择合适的操作路径：

| 用户意图 | 操作 | 工具 |
|---------|------|------|
| 读取/提取内容 | 文本提取 | `python -m markitdown <file>` |
| 修改现有文件 | 解包 → 编辑 XML → 打包 | `unpack.py` → 编辑 → `pack.py` |
| 从零创建 PPTX | 编程生成 | PptxGenJS (Node.js) |
| 模板排版复制 | 分析样式 → 应用 | 解包模板 → 提取规则 → 生成新文档 |

## Workflow

### 1) 读取与分析

```bash
python -m markitdown input.pptx   # 或 .docx / .xlsx
```

PPTX 可生成缩略图网格用于版式分析：

```bash
python scripts/thumbnail.py presentation.pptx
```

### 2) 解包 → 编辑 → 打包

通用三步流程：

```bash
# 解包（自动美化 XML、处理智能引号）
python scripts/office/unpack.py input.pptx unpacked/

# 编辑 unpacked/ 目录下的 XML 文件
# - PPTX: ppt/slides/slide{N}.xml
# - DOCX: word/document.xml
# - XLSX: xl/worksheets/sheet{N}.xml

# 打包（--original 启用 XSD 校验 + 自动修复）
python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

格式专属注意：
- **DOCX**：解包自动合并相邻 runs 并简化 redlines
- **PPTX**：结构编辑后运行 `python scripts/clean.py unpacked/` 清理孤立文件

### 3) PPTX 模板编辑

1. **分析模板**：`thumbnail.py` 看版式 + `markitdown` 看内容
2. **规划映射**：为每段内容选择模板幻灯片，使用多样化布局
3. **解包**：`unpack.py`
4. **结构操作**：
   - 删除不需要的幻灯片：从 `<p:sldIdLst>` 移除
   - 复制幻灯片：`python scripts/add_slide.py unpacked/ slide2.xml`
   - 重排顺序：调整 `<p:sldIdLst>` 中的 `<p:sldId>` 顺序
5. **编辑内容**：修改每个 `slide{N}.xml` 中的文本
6. **清理 + 打包**：`clean.py` → `pack.py`

### 4) PPTX 从零创建（PptxGenJS）

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';

let slide = pres.addSlide();
slide.addText("标题", { x: 0.5, y: 0.5, fontSize: 36, color: "363636", bold: true });

pres.writeFile({ fileName: "output.pptx" });
```

关键规则：
- 颜色不加 `#`：`"FF0000"` ✅ `"#FF0000"` ❌（会损坏文件）
- 用 `bullet: true` 不用 Unicode `•`
- 用 `breakLine: true` 换行
- 每次调用创建新选项对象，不复用

### 5) DOCX 编辑

- 读取：`python -m markitdown document.docx`
- 编辑：解包 → 修改 `word/document.xml` → 打包（`--original` 启用校验和 redlining 检查）
- 模板排版：分析模板样式（字体/字号/间距）→ 将用户内容应用到相同样式结构

### 6) XLSX 编辑

- 读取：`python -m markitdown workbook.xlsx`
- 编辑：解包 → 修改 `xl/` 下的 XML → 打包
- 无格式专属校验器

### 7) QA 检查

```bash
# 内容检查
python -m markitdown output.pptx

# 视觉检查（PPTX）
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

## XML 编辑规范

- 使用 Edit 工具修改 XML，不用 sed/awk/Python 脚本
- Bold 标题和行内标签：`<a:rPr>` 加 `b="1"`
- 列表：`<a:buChar>` / `<a:buAutoNum>`，不用 Unicode 符号
- 智能引号：`&#x201C;` `&#x201D;` `&#x2018;` `&#x2019;`
- 空白保持：`xml:space="preserve"`
- XML 解析器：`defusedxml.minidom`（不用 `xml.etree.ElementTree`）
- 多条目内容：每条独立 `<a:p>` 元素，不串联

## Scripts Reference

| 脚本 | 用途 |
|------|------|
| `scripts/office/unpack.py` | 解包 Office 文件 |
| `scripts/office/pack.py` | 打包 + 校验 + 自动修复 |
| `scripts/office/validate.py` | 独立校验 |
| `scripts/office/soffice.py` | LibreOffice 辅助 |
| `scripts/clean.py` | 清理 PPTX 孤立文件 |
| `scripts/add_slide.py` | 复制/新建幻灯片 |
| `scripts/thumbnail.py` | 缩略图网格 |

## Dependencies

```bash
pip install "markitdown[pptx]" Pillow defusedxml lxml
npm install -g pptxgenjs
```

可选：LibreOffice、Poppler

## Output Contract

操作完成后输出：
1. **操作摘要**：做了什么
2. **文件路径**：输出文件位置
3. **QA 结果**（如适用）

## Notes

- 与 Codex / Claude 版本保持核心工作流一致，措辞适配当前模型
- 脚本路径引用需根据实际部署位置调整
