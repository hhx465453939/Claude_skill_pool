---
description: 单细胞 Seurat FindAllMarkers 结果的细胞类型注释与文献报告生成，一次性产出 R recode 代码和 Markdown 注释报告。
---

# /scrna-celltype-annotation - 单细胞亚群注释与文献报告

你现在调用的是 **单细胞亚群注释与文献报告命令**。它会驱动 `scrna-celltype-annotation` 技能，从 DGE CSV 出发，为每个 cluster 生成带有文献依据的细胞类型注释，并输出标准化 Markdown 报告。

---

## 使用场景

适合这些情况：

- 已经用 Seurat 完成了标准 scRNA-seq 流程（归一化、降维、聚类、FindAllMarkers）
- 手上有每个 cluster 的差异表达结果（`FindAllMarkers` 导出的 CSV）
- 希望系统性地给每个 cluster 做 **major / minor 两层级细胞类型注释**
- 同时需要一份可以放进论文/补充材料的 **Markdown 注释报告**：
  - 包含完整的 R `recode` 注释代码
  - 每个 cluster 注释的文献来源和证据说明

不太适合：

- 还没有稳定的聚类结果或差异分析（建议先在 R/Seurat 里完成基础分析）
- 只想快速看一眼粗略 cell type（可以临时用 marker 可视化手动浏览）

---

## 需要你准备好什么

在使用 `/scrna-celltype-annotation` 之前，请尽量先确定并提供：

1. **DGE / FindAllMarkers 结果 CSV**
   - 文件路径或粘贴内容
   - 列名信息：
     - cluster 列（例如：`cluster`、`seurat_clusters`、`ident`）
     - 基因名列（例如：`gene`、`feature`）
     - 效应量列（例如：`avg_log2FC` / `avg_logFC`）
     - 显著性列（例如：`p_val_adj` / `p_val`）
2. **Seurat 对象与元数据**
   - R 中 Seurat 对象名称（例如：`colon`、`pbmc`）
   - meta.data 中对应 cluster 的列名（例如：`seurat_clusters`）
   - 期望新建的两个列名（默认：`celltype_major` 和 `celltype_minor`）
3. **生物学上下文信息**
   - 物种（mouse / human / rat / 其他）
   - 组织/器官（如 colon、lung、PBMC、tumor microenvironment 等）
   - 疾病或实验模型（如 IBD、肿瘤、针灸造模大鼠等）
   - 是否有希望对标的关键参考论文或 atlas

如果你暂时不清楚某些细节，可以先提供已有信息，剩余部分由助手在对话中循序补问。

---

## 标准工作流程

当你输入 `/scrna-celltype-annotation` 并提供上述信息后，助手会按以下步骤工作：

### 1. 解析 DGE 表格

- 读取 CSV，识别 cluster / gene / 效应量 / 显著性等关键列
- 按 cluster 分组，过滤显著差异基因（例如：`p_val_adj < 0.05` 且 `avg_log2FC > 0`）
- 为每个 cluster 选取 top N（通常 N≈20）个代表性 marker 作为后续判读依据

### 2. 基于 marker 组合做初步 major 分类

- 使用经典 marker 规则，将每个 cluster 粗略映射到若干候选大类（major）：
  - EpC / epithelial、MP / myeloid、T、B / Plasma、EC、Fibroblast、SMC、Neuron 等
- 这一阶段仅作为先验，不被当作最终文献证据

### 3. 调用 MCP 文献工具执行逐 cluster 文献检索

- 针对每个 cluster，构造“`top marker + 组织 + 物种 + single-cell`”的检索 query
- 使用 PubMed / OpenAlex 等 MCP 工具：
  - 搜索相关单细胞研究或 atlas
  - 读取摘要、结果、图注和表格描述
  - 找到与当前 marker 组合高度匹配的细胞类型 / 亚型命名方式
- 在此基础上，为每个 cluster 决定：
  - 一个 **major 注释**（大类）
  - 一个 **minor 注释**（精细亚型，例如 `EpC_goblet_precursor`）
- 同时记录：
  - 对应的论文题目、期刊、年份、PMID/DOI
  - 使用到的证据片段来自哪一部分（Figure / Table / Results / Supplement）

### 4. 生成 R recode 注释代码

- 使用你提供的 Seurat 对象名和 cluster 列名，生成两段可直接运行的注释代码：
  - `object$celltype_major <- recode(object$seurat_clusters, "0" = "EpC", ...)`
  - `object$celltype_minor <- recode(object$seurat_clusters, "0" = "EpC_goblet_precursor", ...)`
- 保证：
  - cluster 编码与 CSV / Seurat 对象保持一致
  - 注释命名规则在整份报告中统一

### 5. 组织 Markdown 注释报告

最终输出的报告会遵守固定骨架，便于直接保存为 `.md` 或插入论文：

1. `## 总结与Recode函数`
   - 说明对象名、cluster 列名、新建列名
   - 给出两套完整的 R `recode` 代码（major / minor）
2. `## 注释概述`
   - 按 major 类型分组，列出包含的 cluster 与 minor 名称
   - 对每类细胞在当前组织/模型中的生物学特征做简要说明
3. `## 各 cluster 注释的文献依据`
   - 每个 cluster 一个小节：
     - 预测细胞类型（major + minor）
     - 关键 marker 基因列表
     - 文献条目（作者/年份/期刊/PMID/DOI）及使用到的证据位置与简要解读

如有不确定性或文献证据不足，都会在对应小节中明确标记为“基于 marker 组合的推断”，不会伪造 PMID/DOI 或图表信息。

---

## 标准输出格式

每次运行 `/scrna-celltype-annotation`，助手会至少输出：

```markdown
## 总结与Recode函数
...（包含 R recode 代码）

## 注释概述
...（按 major 类型归类 cluster）

## 各 cluster 注释的文献依据
...（逐 cluster 说明 marker 与文献证据）
```

同时在对话中简要总结：

- 注释了多少个 cluster
- major 类型的数量与列表
- 主要由文献强支撑的注释 vs 以推断为主的注释各有多少

你可以将这段 Markdown 直接保存为 `*.md` 文件，或拷贝到论文的结果/补充材料中使用。

