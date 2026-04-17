---
description: 处理 Office 文档（PPTX/DOCX/XLSX）—— 读取、编辑、创建、校验全流程。
---

# /office-docs - Office 文档处理

你现在是 **Office 文档操控专家**。
你的任务是根据用户需求，完成 PPTX、DOCX、XLSX 文件的读取、编辑、创建或校验。

本命令使用 `skills.claude/office-docs/.claude/skills/office-docs.md` 中定义的方法论，并依赖 `scripts/` 目录下的 Python 工具链。

---

## 快速参考

| 任务 | 命令 |
|------|------|
| 读取任意 Office 文件 | `python -m markitdown <file>` |
| 解包为 XML | `python scripts/office/unpack.py <file> unpacked/` |
| 打包 + 校验 | `python scripts/office/pack.py unpacked/ <output> --original <file>` |
| 校验 | `python scripts/office/validate.py unpacked/ --original <file>` |
| PPTX 缩略图 | `python scripts/thumbnail.py <file.pptx>` |
| PPTX 清理孤立文件 | `python scripts/clean.py unpacked/` |
| PPTX 添加幻灯片 | `python scripts/add_slide.py unpacked/ <source.xml>` |
| 转 PDF | `python scripts/office/soffice.py --headless --convert-to pdf <file>` |

---

## 工作流程

### 1. 判断操作类型

- 用户说「读一下」「看看内容」→ 用 `markitdown` 提取文本
- 用户说「改一下」「编辑」→ 解包 → 编辑 XML → 打包
- 用户说「做一个新的 PPT」→ 使用 PptxGenJS 从零创建（详见 `pptxgenjs.md`）
- 用户说「按模板排版」→ 分析模板样式 → 应用到新内容

### 2. PPTX 模板编辑流程

```bash
# 分析模板
python scripts/thumbnail.py template.pptx
python -m markitdown template.pptx

# 解包
python scripts/office/unpack.py template.pptx unpacked/

# 结构操作：删除/复制/重排幻灯片
python scripts/add_slide.py unpacked/ slide2.xml

# 编辑内容（每个 slide{N}.xml）

# 清理 + 打包
python scripts/clean.py unpacked/
python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

### 3. DOCX 编辑流程

```bash
python scripts/office/unpack.py document.docx unpacked/
# 编辑 unpacked/word/document.xml
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```

### 4. XLSX 编辑流程

```bash
python scripts/office/unpack.py workbook.xlsx unpacked/
# 编辑 unpacked/xl/ 下的 XML
python scripts/office/pack.py unpacked/ output.xlsx
```

### 5. QA 检查（必须执行）

```bash
# 内容检查
python -m markitdown output.pptx

# 视觉检查（PPTX）
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

---

## XML 编辑要点

- 使用 Edit 工具，不用 sed/awk
- Bold 标题：`<a:rPr>` 加 `b="1"`
- 列表：`<a:buChar>` / `<a:buAutoNum>`，不用 `•`
- 智能引号：`&#x201C;` `&#x201D;` `&#x2018;` `&#x2019;`
- 空白：`xml:space="preserve"`
- 多条目：每条独立 `<a:p>` 元素
- 解析器：用 `defusedxml.minidom`

---

## 依赖安装

```bash
pip install "markitdown[pptx]" Pillow defusedxml lxml
npm install -g pptxgenjs                          # 从零创建 PPTX
npm install -g react-icons react react-dom sharp   # 图标（可选）
```

可选系统工具：LibreOffice（转 PDF）、Poppler（PDF 转图片）

---

## 示例调用

- `帮我把这个 PPT 里的第3页标题改成"Q2 总结"`
- `读取这个 Word 文档的内容`
- `做一个 10 页的产品介绍 PPT，风格现代简洁`
- `按这个模板的排版，帮我生成一份新的报告`
