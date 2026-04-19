---
name: scrna-celltype-annotation
description: 基于 Seurat FindAllMarkers 差异表达结果与文献 MCP 工具，对单细胞亚群进行 major/minor 细胞类型注释并生成带 R recode 代码和文献依据的 Markdown 报告。
version: 1.0.0
---

# 单细胞亚群注释与文献报告技能

## Overview

这个技能用于在已经完成 Seurat 分析（特别是 `FindAllMarkers` 或 `FindMarkers`）的单细胞转录组数据基础上，结合文献检索 MCP 工具（如 PubMed / OpenAlex），为每个 cluster/亚群给出：

- **两个层级的细胞类型注释**：
  - **major 注释**：若干生物学大类（如 EpC、TC、MP、T、EC、FC、SMC、NR、EE、B、PC、其他免疫细胞等）
  - **minor 注释**：精细到具体亚型的细胞名称（如 `EpC_goblet_precursor`、`Macrophage_inflammatory_resident`）
- **一份结构化 Markdown 报告**：
  - 部分 1：R 中可直接使用的 `recode` 注释代码（major / minor 两套）
  - 部分 2：每个 cluster 注释的**文献依据说明**，包括引用的论文、PMID/DOI、期刊与年份，以及“哪一段文字/哪张图/哪张表支持该解释”。

适用典型场景：

- 已有 Seurat 对象和 `FindAllMarkers` 结果，想要系统、可追溯地完成细胞类型注释
- 希望在论文或报告中同时呈现「注释代码 + 注释依据」的一体化说明
- 需要在不同项目之间复用统一的注释风格与输出格式

---

## 输入要求

使用本技能前，请确保用户已经准备好以下信息（若缺失，需要在对话中主动追问）：

- **差异表达结果 CSV 文件**（通常是 `FindAllMarkers` 的输出），推荐至少包含：
  - cluster/ident 列（例如 `cluster`、`seurat_clusters` 或 `cluster_id`）
  - 基因名列（例如 `gene` 或 `features`，最好是 HGNC/官方 symbol）
  - 差异指标列：如 `avg_log2FC` 或 `avg_logFC`
  - 统计显著性：如 `p_val_adj` / `p_val`
  - 表达比例：如 `pct.1` / `pct.2`（可选但推荐）
- **Seurat 对象信息**：
  - R 中对象名（例如 `colon`、`pbmc`）
  - 表示 cluster 的 meta.data 列名（例如 `seurat_clusters`、`RNA_snn_res.0.8` 等）
- **生物学上下文元信息**：
  - 物种（mouse / human / rat / 其他）
  - 组织 / 器官（如 colon、lung、PBMC、tumor microenvironment 等）
  - 疾病或实验模型（如 IBD、tumor、针灸造模等）
  - 文库类型 / 技术（如 10x Genomics、Smart-seq2，可选）
- （可选）**先验知识**：
  - 已知的 marker gene 列表
  - 已参考或计划对标的基准文献

---

## 可用 MCP 文献工具（建议）

为保证注释“有据可依”，本技能应系统性调用以下 MCP 工具（名称为概念层，具体实现由宿主环境映射）：

### PubMed 系列

- `pubmed_search`：根据关键词（基因组合 + 组织 + single-cell）检索相关文献
- `pubmed_quick_search`：快速获取少量候选文献
- `pubmed_get_details`：根据 PMID 获取详细信息（题目、摘要、期刊、年份等）
- `pubmed_extract_key_info`：提取摘要、结果中的关键信息，辅助判断 marker–细胞类型关系
- `pubmed_cross_reference`：查找相似/引用/被引用文献（用于补充佐证）

### OpenAlex / 其他学术工具

- `openalex_search`：按标题关键词（包含基因名、组织、single-cell）搜索文章
- `openalex_get_work`：获取单篇文章的详细元数据和摘要
- `openalex_detect_fulltext` / `openalex_download_fulltext`：检测并下载开放获取全文（如需要更精细证据）

> 原则：**优先使用 PubMed/OpenAlex 的真实结果，不得凭空杜撰 PMID/DOI 或伪造图表位置。** 如果文献证据不足，必须在报告中明确标记为“推断性注释”而非“文献直接支持”。

---

## 标准工作流（Workflow）

### 1. 解析需求与上下文

1. 从用户获取：
   - DGE CSV 路径 / 内容
   - Seurat 对象名与 cluster 列名
   - 物种、组织、疾病/模型等关键信息
   - 是否有指定的参考论文（如某篇高质量 atlas 作为主要对标）
2. 明确输出偏好：
   - recode 的目标列名称（默认：`celltype_major` / `celltype_minor`）
   - cluster 是否为字符串/数字（按原始 CSV/Seurat 对象保持一致）

### 2. 读取并整理 DGE 结果

1. 读取 CSV，确认关键列是否存在：
   - 若列名不标准（如 `cluster.id`、`feature`），需记录实际列名并在后文统一使用。
2. 按 cluster 分组，构建每个 cluster 的 marker 概览表（**保证每个 cluster 至少有 30 个 log2FC 较高的基因被纳入后续分析**）：
   - 第一步：按显著性过滤上调基因（例如 `p_val_adj < 0.05` 且 `avg_log2FC > 0`），按 `avg_log2FC` 或其他效应量降序排列。
   - 若显著上调基因数量 **≥ 30**：可直接在这些基因中选取 top N（例如 30–100 个，默认 N≈50，可根据上下文调整）。
   - 若显著上调基因数量 **< 30**：在保留全部显著基因的前提下，**继续按 `avg_log2FC` 从高到低补充分子**，即便其 `p_val_adj` 不显著，直到该 cluster 至少包含 30 个上调基因。
   - 需要在后续报告中对“仅由 log2FC 高但显著性不足的 marker”做出说明，可在文献依据部分标记为“探索性 marker（非严格显著）”，避免它们被误解为高置信度差异基因。
3. 可选：根据 `pct.1` / `pct.2` 等指标，剔除广泛表达的 housekeeping 基因，突出特异性 marker（在保证**不少于 30 个候选 marker**的前提下进行该步筛选）。

### 3. 先验规则 + marker 组合的初步判读

在调用 MCP 之前，先基于常识规则和 marker 组合进行粗分类，为后续文献检索提供先验：

- 识别典型大类：
  - Epithelial: EPCAM, KRT8/18, MUC 系列等
  - T cells: CD3D/E, CD4, CD8A/B, TRAC, IL7R 等
  - B/Plasma: MS4A1(CD20), CD79A/B, MZB1, XBP1, SDC1(CD138) 等
  - Myeloid/Macrophage: LYZ, CD68, CSF1R, ITGAM, MRC1 等
  - Neutrophil: S100A8/A9, CXCR2, CSF3R 等
  - Endothelial: PECAM1, VWF, KDR, CLDN5 等
  - Fibroblast/Stromal: COL1A1, COL3A1, DCN, PDGFRA 等
  - Smooth muscle: ACTA2, TAGLN, MYH11 等
  - Neuronal/Glial: SNAP25, RBFOX3, SLC17A7, GFAP 等
- 基于这些特征，为每个 cluster 生成一个**候选 major 类别**列表（可多候选，带置信度）。

> 这一阶段的结论属于“先验推断”，不得直接作为最终文献依据，后续必须通过 MCP 检索进行校正或佐证。

### 4. 逐 cluster 调用 MCP 进行文献检索与证据收集

对每个 cluster，执行以下步骤：

1. 构建检索 query：
   - 组合：`(top marker genes) + (tissue/organ) + (species) + "single-cell" / "single cell" / "scRNA-seq"`
   - 如有候选 cell type 名称（例如“goblet cell”），可加入第二轮检索以精细确认。
2. 使用 PubMed 和/或 OpenAlex：
   - 首先用 `pubmed_search` / `openalex_search` 获取 5–10 篇候选文献
   - 过滤出与目标组织/物种最匹配的文章
3. 对每篇高相关文献：
   - 调用 `pubmed_get_details` / `openalex_get_work` / `pubmed_extract_key_info`
   - 在**摘要、结果、图注、补充材料描述**中寻找：
     - 该细胞类型的标准/特征 marker 列表
     - 该亚型在单细胞图谱中的命名方式（如“Inflammatory macrophages”、“Goblet cell precursors”）
4. 根据文献证据，为该 cluster 给出：
   - **minor 注释名称**（例如 `EpC_goblet_precursor`）
   - **major 注释名称**（例如 `EpC`）
   - **marker & 文献证据说明**：
     - 指出本 cluster 的哪些 marker 与论文中的描述对应
     - 引用具体位置：如 “Figure 2b”, “Results, paragraph 3”, “Table S4”

若某个 cluster 文献证据不足或仅能间接推断：

- 可以给出合理的推断注释，但必须在报告中明确为“基于 marker 组合的推断，尚缺直接单细胞文献支持”。

### 5. 生成 R recode 注释代码

根据每个 cluster 的 major / minor 结论，生成可直接在 R 中使用的 recode 代码，输出时需要：

- 保持 cluster 编码与原始 `Seurat` 对象一致（字符/数字都需一致）
- 提前在报告顶部说明：
  - 对象名（如 `colon`）
  - cluster 列名（如 `seurat_clusters`）
  - 新增列名（默认 `celltype_major` / `celltype_minor`，可按用户要求调整）

示例结构（仅为格式示意，实际内容由分析结果填充）：

```r
# 单细胞对象 major 细胞类型注释
colon$celltype_major <- recode(colon$seurat_clusters,
  "0" = "EpC",
  "1" = "TC",
  "2" = "MP",
  ...
)

# 单细胞对象 minor 细胞亚型注释
colon$celltype_minor <- recode(colon$seurat_clusters,
  "0" = "EpC_goblet_precursor",
  "1" = "TC_matrix_secreting",
  "2" = "Macrophage_inflammatory_resident",
  ...
)
```

> 如用户额外要求 CellCall / CellChat 等工具专用格式，可在 minor 注释基础上追加一份“点号分隔”的 recode 代码，但不作为本技能的硬性输出要求。

### 6. 组织 Markdown 注释报告

报告必须至少包含两个核心部分，结构建议如下：

1. **`## 总结与Recode函数`**
   - 简要说明：
     - Seurat 对象名
     - cluster 列名
     - major/minor 注释列名
   - 给出两段完整的 R `recode` 代码（major / minor）
2. **`## 注释概述` + 各 major 类型小节**
   - 按 major 类型组织，例如：
     - `### 1. EpC (上皮细胞 - Epithelial cells)`
     - `### 2. TC (特洛细胞 - Telocytes)`
     - ...
   - 每个 major 小节中：
     - 清单列出包含的 cluster 与对应 minor 名称
     - 用 2–4 句概括该类细胞在当前组织/模型中的生物学功能
3. **`## 各 cluster 注释的文献依据`**
   - 对每个 cluster 使用固定模板，例如：
     - `### Cluster 0: EpC_goblet_precursor (Major: EpC)`
       - **预测细胞类型**：简要解释
       - **关键 marker 基因**：列出用于判定的 5–10 个 marker
       - **文献依据**：
         - `- [作者等, 年, 期刊, PMID: xxxx, DOI: yyyy] - 在 Figure / Table / Results 中如何描述该亚群及 marker`
         - 可附上简明引用原文或精准转述（禁止虚构）

必要时可在文末追加：

- `## 方法说明与局限性`
  - 说明 marker 选择阈值、MCP 工具使用情况、可能的交叉反应标记等

---

## Output Contract（必须遵守）

当技能执行完成时，**必须至少输出一个完整的 Markdown 文档片段**，可直接保存为 `*.md` 用于论文或补充材料，结构应满足：

```markdown
## 总结与Recode函数
...（major / minor 两套 recode 代码，带对象名和列名说明）

## 注释概述
...（按 major 类型归纳各 cluster，解释生物学特征）

## 各 cluster 注释的文献依据
...（逐 cluster 给出 marker + 文献信息 + 证据位置）
```

在执行环境支持文件写入时，应优先将**完整 Markdown 报告直接写入当前项目根目录**（例如 `./scrna_celltype_annotation_report.md` 或用户指定的文件名），在 chat 界面仅给出：

- 报告文件的相对路径/文件名
- 报告结构与主要结论的简短摘要

后续与用户的微调与修改，应**围绕该报告文件进行增量更新**（视为“注释结果的单一事实来源”），避免每次在对话中重复输出整篇长报告。

同时在对话中补充简要的执行摘要，包括：

- 总共注释了多少个 cluster
- major 类型数量与名称
- 文献支持充分 vs 主要依赖推断的 cluster 数量

---

## 错误处理与保守性原则

- **找不到合适文献时**：
  - 明确标注为“暂未找到直接单细胞文献支持，基于 marker 组合推断”
  - 不输出伪造的 PMID/DOI 或不确定的期刊信息
- **多篇文献结论存在差异时**：
  - 优先近期、高影响力或与当前组织/疾病背景最匹配的研究
  - 在报告中简要说明存在不同观点，给出你采用该注释的理由
- **marker 模糊或跨类型共表达时**：
  - 必须在“文献依据”小节中解释该不确定性
  - 尽量结合多个 marker 组合与功能描述，而非单基因命名

遵循以上约束，可以最大限度减少幻觉，保证单细胞注释结果在科研场景中的可追溯性与可复现性。

