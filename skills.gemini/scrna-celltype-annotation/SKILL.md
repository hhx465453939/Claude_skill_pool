---
name: scrna-celltype-annotation
description: 基于 Seurat FindAllMarkers 差异表达结果与文献 MCP 工具，对单细胞亚群进行 major/minor 细胞类型注释并生成带 R recode 代码和详细文献依据的 Markdown 报告。
version: 1.0.0
---

# 单细胞亚群注释与文献报告（Gemini 版）

这个技能为 Gemini 模型提供一套标准化流程，用于：

- 读取经过 Seurat 流程（特别是 `FindAllMarkers`）处理好的单细胞 DGE 表格（CSV）
- 利用 MCP 文献检索工具（如 PubMed / OpenAlex）为每个 cluster/亚群做 **major / minor 两层级注释**
- 输出一份包含 **R recode 注释代码 + 文献依据说明** 的 Markdown 报告

---

## Overview

典型使用场景：

- 用户已经完成 Seurat 聚类与差异分析，只缺“高质量细胞注释 + 文献支撑报告”
- 希望在论文或项目文档中直接粘贴：
  - `recode` 注释代码
  - 每个 cluster 注释的文献依据（带 PMID/DOI 与具体证据描述）

这个技能强调：

- **MCP first**：优先通过 PubMed/OpenAlex 等 MCP 工具获取真实文献信息
- **两层级注释**：major（大类）+ minor（精细亚型）
- **报告结构固定**：便于自动化集成与后续复用

---

## Required Inputs

1. **DGE / FindAllMarkers 结果 CSV**
   - 必备列（名称可自定义，但需能识别）：
     - cluster / ident（cluster ID）
     - gene / feature（基因 symbol）
     - 效应量列（如 `avg_log2FC` / `avg_logFC`）
     - 显著性列（如 `p_val_adj` / `p_val`）
   - 可选推荐列：
     - 表达比例：`pct.1` / `pct.2`
2. **Seurat 对象元信息**
   - R 对象名（如 `colon`、`pbmc`）
   - cluster 列名（如 `seurat_clusters`）
   - 目标注释列名（默认：`celltype_major` / `celltype_minor`）
3. **生物学上下文**
   - 物种（mouse / human / rat / other）
   - 组织/器官（如 colon、lung、PBMC）
   - 疾病或实验模型（如 IBD、tumor、针灸造模等）
   - 是否有指定的重要参考文献（如某 atlas 论文）

---

## MCP Tools (Conceptual)

### PubMed 系列

- `pubmed_search` / `pubmed_quick_search`：按“marker 组合 + 组织 + single-cell”检索候选文献
- `pubmed_get_details`：获取题目、摘要、期刊、年份、PMID 等
- `pubmed_extract_key_info`：抽取摘要/结果中的关键信息
- `pubmed_cross_reference`：查找相似或相关研究

### OpenAlex / 其他

- `openalex_search`：用标题/关键词检索相关单细胞文献
- `openalex_get_work`：查看文章元数据与摘要
- `openalex_detect_fulltext` / 其他全文工具：需要精确图注/表格描述时可调用

> 实现时应调用真实的 MCP 工具，而非凭空编造文献信息。禁止虚构 PMID/DOI 或伪造图表内容。

---

## Workflow

### 1. Parse DGE Table

1. 读取 CSV，识别：
   - cluster 列名
   - gene 列名
   - 效应量 & 显著性列名
2. 按 cluster 分组，过滤显著差异基因（如 `p_val_adj < 0.05` 且 `avg_log2FC > 0`），取每个 cluster 的 top N marker（默认 N≈20）。

### 2. Initial Major Classification by Marker Rules

基于经典 marker 组合，对每个 cluster 进行初步 major 类型判定（仅供先验）：

- EpC：EPCAM、KRT8/18、MUC 系列…
- Myeloid / Macrophage：LYZ、CD68、CSF1R、MRC1…
- T：CD3D/E、CD4、CD8A/B、IL7R、GZMB…
- B / Plasma：MS4A1、CD79A/B、MZB1、XBP1、SDC1…
- Endothelial：PECAM1、VWF、KDR、CLDN5…
- Fibroblast/Stromal：COL1A1、COL3A1、DCN、PDGFRA…
- Smooth muscle：ACTA2、TAGLN、MYH11…
- Neuron / Glia：SNAP25、RBFOX3、GFAP…

输出每个 cluster 的候选 major 类型列表，为后续 MCP 检索提供上下文。

### 3. Literature Retrieval per Cluster

对于每个 cluster：

1. 构造检索 query：
   - 组合 top marker + 组织 + 物种 + (“single-cell” / “scRNA-seq”) ± 预期 cell type 关键词
2. 调用 PubMed/OpenAlex 检索候选文献：
   - 首先获取 5–10 篇最相关的单细胞/组织特异研究
3. 对重点文献：
   - 提取：
     - 该细胞类型/亚型的 marker 列表
     - 单细胞图谱中 cluster 的命名方式
     - 与当前 cluster marker 高度吻合的片段（图注/结果/表格）
4. 基于 marker + 文献证据，确定：
   - **minor 注释名**（精细亚型）
   - **major 注释名**（大类）

若证据不足以支持精细亚型：

- 使用较宽泛的 minor 名称，并在报告中标注为“基于 marker 组合推断，缺乏直接单细胞文献支持”。

### 4. Generate R recode Code

根据每个 cluster 的 major/minor 结论，生成：

```r
# major 注释
object$celltype_major <- recode(object$seurat_clusters,
  "0" = "EpC",
  "1" = "TC",
  ...
)

# minor 注释
object$celltype_minor <- recode(object$seurat_clusters,
  "0" = "EpC_goblet_precursor",
  "1" = "TC_matrix_secreting",
  ...
)
```

要求：

- cluster 编码与原始 Seurat 对象完全一致
- 在报告开头注明对象名、cluster 列名和两个注释列名

### 5. Compose Markdown Report

报告应至少包含：

1. `## 总结与Recode函数`
   - 说明对象名 & 列名
   - 输出两段完整的 R `recode` 代码（major / minor）
2. `## 注释概述`
   - 按 major 类型分节
   - 每个 major 小节：
     - 列出包含的 cluster 和 minor 名称
     - 用 2–4 句描述该大类的生物学功能
3. `## 各 cluster 注释的文献依据`
   - 每个 cluster 一个小节，包含：
     - 预测细胞类型（major + minor）
     - 关键 marker 基因列表
     - 文献依据条目：
       - `[作者等, 年, 期刊, PMID: xxxx, DOI: yyyy] - 来自哪一部分（图/表/结果）的证据 + 简要描述`

可选：在文末添加“方法说明与局限性”小节。

---

## Output Contract

完成任务时，Gemini 模型必须输出：

1. **一段完整的 Markdown 文档内容**，结构至少包含：

```markdown
## 总结与Recode函数
...（major / minor 两套 R recode 代码）

## 注释概述
...（按 major 类型归类 cluster）

## 各 cluster 注释的文献依据
...（逐 cluster 说明 marker 与文献证据）
```

2. 简短执行摘要：
   - 注释的 cluster 数量
   - major 类型数量与列表
   - 文献支持充分 vs 推断为主的 cluster 数量

---

## Safety & Error Handling

- **禁止伪造文献信息**：不得虚构 PMID/DOI/期刊名或伪造“Figure X 结论”。
- **证据不足时**：
  - 明确标记为“基于 marker 组合的推断”
  - 鼓励用户在后续实验或更精细分析中进一步验证
- **冲突结果时**：
  - 说明不同文献的差异
  - 解释当前选择该注释方案的理由（如更贴合组织/疾病背景、样本量更大等）

遵循以上流程，Gemini 模型即可稳定地为单细胞项目生成可追溯、可复现的细胞类型注释与文献报告。

