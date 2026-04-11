---
name: office-docs
description: "处理 Microsoft Office Open XML 文件 — .pptx（演示文稿/幻灯片）、.docx（Word 文档）、.xlsx（Excel 表格）。当用户提到或需要处理这些格式时触发：读取/提取文本、编辑、从模板或从零创建、解包/打包 XML、校验。关键词：.pptx, .docx, .xlsx, presentation, deck, slides, Word document, Excel, spreadsheet, PowerPoint, 幻灯片, 演示文稿, 表格。"
---

# Office Documents (PPTX, DOCX, XLSX)

## Overview

该 skill 提供对 Microsoft Office Open XML 格式（PPTX、DOCX、XLSX）的完整操控能力，包括：

- **读取/提取文本**：使用 `markitdown` 将 Office 文件转换为可读文本
- **解包/编辑/打包**：将 Office 文件（本质是 ZIP 包）解包为 XML，直接编辑后重新打包
- **校验与自动修复**：基于 OOXML 标准的 XSD 校验 + 文件引用完整性检查
- **从模板创建**：基于现有模板文件复制/修改幻灯片或文档内容
- **从零创建 PPTX**：使用 PptxGenJS（Node.js）生成全新演示文稿

## Quick Reference

| 任务 | PPTX | DOCX | XLSX |
|------|------|------|------|
| 读取/提取文本 | `python -m markitdown file.pptx` | `python -m markitdown file.docx` | `python -m markitdown file.xlsx` |
| 解包编辑 | `python scripts/office/unpack.py file.pptx unpacked/` | `python scripts/office/unpack.py file.docx unpacked/` | `python scripts/office/unpack.py file.xlsx unpacked/` |
| 打包输出 | `python scripts/office/pack.py unpacked/ out.pptx --original file.pptx` | `python scripts/office/pack.py unpacked/ out.docx --original file.docx` | `python scripts/office/pack.py unpacked/ out.xlsx` |
| 校验 | `python scripts/office/validate.py unpacked/ --original file.pptx` | `python scripts/office/validate.py unpacked/ --original file.docx` | 仅解包/打包（无 schema 校验） |
| 格式专属工具 | `thumbnail.py`, `add_slide.py`, `clean.py` | merge_runs, simplify_redlines（解包自动执行） | — |

## Workflow

### 1) 读取与分析

```bash
python -m markitdown input.pptx   # 或 .docx / .xlsx
```

对于 PPTX，还可以生成幻灯片缩略图网格用于快速可视化分析：

```bash
python scripts/thumbnail.py presentation.pptx
```

### 2) 解包 → 编辑 → 打包（通用流程）

```bash
# 解包
python scripts/office/unpack.py input.pptx unpacked/

# 编辑 unpacked/ 下的 XML（word/, ppt/, xl/ 按格式区分）

# 打包（使用 --original 启用校验）
python scripts/office/pack.py unpacked/ output.pptx --original input.pptx
```

- **DOCX** 解包时默认合并相邻 runs 并简化 redlines；可用 `--merge-runs false` 关闭
- **PPTX** 结构编辑后，在打包前运行 `python scripts/clean.py unpacked/` 清理孤立文件

### 3) PPTX 专属操作

#### 模板编辑工作流

1. **分析模板**：`python scripts/thumbnail.py template.pptx` + `python -m markitdown template.pptx`
2. **规划幻灯片映射**：为每段内容选择合适的模板幻灯片。使用多样化布局——避免每页重复同一文字密集型版式
3. **解包**：`python scripts/office/unpack.py template.pptx unpacked/`
4. **结构操作**（亲自完成，不用 subagent）：
   - 删除不需要的幻灯片（从 `<p:sldIdLst>` 移除）
   - 复制要复用的幻灯片（`add_slide.py`）
   - 在 `<p:sldIdLst>` 中重排顺序
5. **编辑内容**：更新每个 `slide{N}.xml` 中的文本（可用 subagent 并行编辑）
6. **清理**：`python scripts/clean.py unpacked/`
7. **打包**：`python scripts/office/pack.py unpacked/ output.pptx --original template.pptx`

#### 从零创建（PptxGenJS）

使用 Node.js 的 PptxGenJS 库从零构建演示文稿：

```javascript
const pptxgen = require("pptxgenjs");
let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
let slide = pres.addSlide();
slide.addText("Hello World!", { x: 0.5, y: 0.5, fontSize: 36, color: "363636" });
pres.writeFile({ fileName: "output.pptx" });
```

关键注意事项：
- 颜色值不加 `#` 前缀：`color: "FF0000"` ✅，`color: "#FF0000"` ❌（会损坏文件）
- 使用 `bullet: true` 而非 Unicode 符号 `•`
- 使用 `breakLine: true` 换行
- 每次调用创建新的选项对象，不要复用（PptxGenJS 会就地修改对象）

#### 设计原则

不要制作无聊的幻灯片。使用内容驱动的配色方案（一个主色、1-2 个辅助色、一个强调色），深浅对比，统一视觉母题。每页幻灯片都需要视觉元素（图片、图表、图标或形状）。

#### QA（必需）

假设输出存在问题。内容检查：`python -m markitdown output.pptx` 并搜索占位符。视觉检查：转换为图片后用 subagent 检查重叠、溢出、对齐、边距问题。

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

### 4) DOCX 专属操作

- **读取**：`python -m markitdown document.docx`
- **编辑**：解包 → 编辑 `unpacked/word/document.xml` → 打包（使用 `--original` 启用校验和 redlining 检查）

#### Word 模板排版复制

当用户提供模板文档时，分析模板的排版规则（段落样式、字体/字号/颜色、间距/缩进），然后将用户内容应用到相同的样式结构中，生成视觉上与模板一致的新文档。

工作流：读取模板 → 提取排版规则 → 生产新文档 → 检查排版一致性。

### 5) XLSX 专属操作

- **读取**：`python -m markitdown workbook.xlsx`
- **编辑**：解包 → 编辑 `unpacked/xl/` 下的 XML → 打包。无格式专属校验器。

### 6) XML 编辑规范

- **使用 Edit 工具**，不用 sed 或 Python 脚本修改 XML
- **Bold 所有标题与行内标签**：在 `<a:rPr>` 上使用 `b="1"`
- **不使用 Unicode 项目符号**（`•`），使用 `<a:buChar>` 或 `<a:buAutoNum>`
- **智能引号**：添加新文本时使用 XML 实体（`&#x201C;`, `&#x201D;` 等）
- **空白保持**：带前导/尾随空格的 `<a:t>` 需加 `xml:space="preserve"`
- **XML 解析**：使用 `defusedxml.minidom`，不用 `xml.etree.ElementTree`（会破坏命名空间）
- **多项内容**：为每个条目创建独立的 `<a:p>` 元素，不要串联到一个字符串中

## Scripts Reference

| 脚本 | 用途 |
|------|------|
| `scripts/office/unpack.py` | 解包 Office 文件，美化 XML，处理智能引号 |
| `scripts/office/pack.py` | 打包目录为 Office 文件，含校验与自动修复 |
| `scripts/office/validate.py` | 独立校验工具（XSD + 文件引用 + 唯一 ID 等） |
| `scripts/office/soffice.py` | LibreOffice 辅助器（处理沙盒环境） |
| `scripts/clean.py` | 清理 PPTX 中未引用的幻灯片/媒体/关系 |
| `scripts/add_slide.py` | 复制幻灯片或从 layout 创建新幻灯片 |
| `scripts/thumbnail.py` | 生成幻灯片缩略图网格 |

## Dependencies

```bash
pip install "markitdown[pptx]" Pillow defusedxml lxml
npm install -g pptxgenjs         # 从零创建 PPTX
npm install -g react-icons react react-dom sharp  # 图标渲染（可选）
```

系统工具（可选）：
- LibreOffice (`soffice`) — PDF 转换
- Poppler (`pdftoppm`) — PDF 转图片用于 QA

## Output Contract

完成 Office 文档操作后，应输出：

1. **操作摘要**：描述做了什么（读取/编辑/创建）
2. **文件路径**：明确输出文件的位置
3. **QA 结果**（如适用）：内容检查与视觉检查的结果
