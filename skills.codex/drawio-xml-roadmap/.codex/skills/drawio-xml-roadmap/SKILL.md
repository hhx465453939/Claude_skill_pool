---
name: drawio-xml-roadmap
description: 基于 draw.io .drawio XML 结构设计并生成可导入的路线图/流程图，严格遵守 mxfile/mxCell 模板与配色布局约定，避免“Invalid file data”等解析错误。
---

# Draw.io XML Roadmap Designer

## Overview

该 skill 用于在开发/研究流程中，将「文字版路线图 / 流程说明」系统化转换为 **可直接导入 draw.io Desktop 的 `.drawio` XML 文件**。  
它遵循 `drawio-xml-roadmap-format` 规则中约定的：

- 顶层结构：`<mxfile><diagram><mxGraphModel><root> ... </root></mxGraphModel></diagram></mxfile>`
- 基础单元：`id="0"` 与 `id="1"` 两个根节点
- 节点（步骤）与连线（edges）的 mxCell 写法
- 布局与配色约定（颜色映射到阶段类型）

适用场景包括但不限于：

- 将数据/模型/产品迭代路线图输出为 `.drawio` 文件
- 将复杂 pipeline（如生信分析、MLOps 流水线）转为可视化流程图
- 为项目规划、技术方案、架构演进生成可编辑的路线图草图

## Workflow

### 1) 明确路线图主题与受众

- 识别本次路线图的**主题**：如「scRNA 分析 pipeline」「产品迭代计划」「系统架构演进」等。
- 确认主要**受众**：研发、产品、运营或跨团队协作，决定用词粒度（更偏技术 / 更偏业务）。
- 提炼一句话目标：`本图要让谁在 30 秒内搞懂什么？`

### 2) 抽取阶段与关键节点

- 从用户自然语言描述或文档中抽取：
  - 主干阶段（3–8 个）：例如「数据预处理与质控」「特征工程」「建模与调参」「评估与上线」。
  - 每个阶段下 1–3 个关键子步骤或工具。
- 使用简短、动词开头的中文标签，例如：
  - 「导入原始数据」
  - 「质控与过滤」
  - 「聚类与可视化」
- 在内部构建节点表：

```markdown
| 节点 ID | 类型       | 标签                     | 所属阶段/分组 |
|--------|------------|--------------------------|---------------|
| STEP_1 | main-stage | 数据预处理与质控         | -             |
| STEP_2 | sub-step   | 细胞过滤与标准化         | STEP_1        |
| STEP_3 | main-stage | 特征选择与降维           | -             |
```

### 3) 规划布局与颜色映射

遵循 `drawio-xml-roadmap-format` 中的布局建议：

- 主干路线：自上而下，保持固定垂直间距（例如 `y += 100`）。
- 分支步骤：放在主干左右，使用相对较小的矩形并通过 orthogonal 边连接到主干。
- 颜色映射建议（可按需调整但要保持全图一致）：
  - 主阶段：`fillColor=#f8cecc;strokeColor=#b85450;`
  - 子步骤/工具：`fillColor=#dae8fc;strokeColor=#6c8ebf;`
  - 计算/建模：`fillColor=#fff2cc;strokeColor=#d6b656;`
  - 验证/集成：`fillColor=#e1d5e7;strokeColor=#9673a6;`

在内部为每个节点分配坐标与尺寸（通常宽 120–160，高 60–80）：

```markdown
| 节点 ID | x    | y    | width | height |
|--------|------|------|-------|--------|
| STEP_1 | -640 |  20  | 120   | 60     |
| STEP_3 | -640 | 120  | 120   | 60     |
```

### 4) 生成 mxCell 节点与连线

根据节点表与布局信息，生成对应的 mxCell XML：

- 节点（vertex）示例：

```xml
<mxCell id="STEP_1" parent="1" vertex="1"
  style="rounded=0;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;"
  value="数据预处理与质控">
  <mxGeometry x="-640" y="20" width="140" height="60" as="geometry"/>
</mxCell>
```

- 连线（edge）示例：

```xml
<mxCell id="EDGE_1_3" parent="1" edge="1" source="STEP_1" target="STEP_3"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

生成时必须遵循：

- **文件首字节必须是 `<mxfile`**，不能有 BOM、空行或注释。
- 不要使用 `<!-- ... -->` 注释。
- 节点 `value` 文本内如有 `<`, `>`, `&`, `"` 等字符，必须进行 XML 转义：
  - `&` → `&amp;`
  - `<` → `&lt;`
  - `>` → `&gt;`
  - `"` → `&quot;`

### 5) 包裹为完整 mxfile 结构

最终将所有 `<mxCell ...>` 放入 `<root>` 中，并包裹为完整结构，例如：

```xml
<mxfile host="Electron" version="29.x.x">
  <diagram name="第 1 页" id="DIAGRAM_ID">
    <mxGraphModel grid="1" gridSize="10" page="1" pageWidth="827" pageHeight="1169">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- 这里插入节点与连线 mxCell -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 6) 校验与导入建议

- 快速自检：
  - 是否存在 `id="0"` 与 `id="1"` 两个基础 cell？
  - 所有 `edge` 的 `source` / `target` 是否都指向已定义的节点 ID？
  - 是否无 XML 注释与未转义的特殊字符？
  - 文件开头是否直接从 `<mxfile` 开始？
- 推荐导入步骤（给人类用户）：
  - 将 XML 内容保存为 `*.drawio` 文件（确保文件内容以 `<mxfile` 开始）。
  - 在 draw.io Desktop 中通过「文件 -> 打开」或拖拽方式导入。
  - 若遇到「Invalid file data」，优先检查是否保存到了应用安装目录下，必要时移动到桌面或文档目录后再次打开。

## Output Contract

完成一次 skill 调用时，至少输出以下两部分内容：

```markdown
## 路线图结构说明
- 主题与受众：...
- 主干阶段列表（含排序与含义）：...
- 关键节点与分支说明（表格或列表）：...

## Draw.io XML (.drawio)
```xml
<mxfile ...>
  ...
</mxfile>
```
```

- `路线图结构说明` 面向人类阅读，帮助理解节点含义与布局决策。
- `Draw.io XML (.drawio)` 必须是**可直接保存为 `.drawio` 的完整 XML**，不夹杂 Markdown 标记与额外注释。

## Resources

- 规则文档：`drawio-xml-roadmap-format`（draw.io .drawio XML roadmap/flowchart output format 约定）
- 相关工具：draw.io Desktop / diagrams.net 在线版（用于导入与后续编辑）

