---
name: deep-research
description: 深度调研技能 - 完全内置的多 Agent 并行执行引擎，支持引用管理、文件发送、轻量量化验证和实时进度反馈。支持 2-8 个内置 agent 同时工作，大幅提升 Token 使用效率和执行速度。
version: 2.3.0
---

# Deep Research - 深度调研技能（引用管理 + 文件发送 + 轻量量化验证）

这是一个**完全内置**、支持**引用管理**、**文件发送**和**轻量量化验证**的多 Agent 并行执行引擎，用于处理需要大量信息收集、多源验证、闭环研究的复杂话题。

## Workspace 对接规则

在当前 workspace 内，本 skill 应直接接入统一 task session 和多 agent bridge，而不是把中间过程散落在 `report/` 根目录。

**进入方式**：

```bash
bash workspace/scripts/deep-research-bootstrap.sh "<task-slug>" "<reason>" \
  --objective "<goal>" \
  --deliverable "<deliverable>" \
  --scope "<scope>"
```

默认会完成三件事：
- 建立 task session 对接
- 写入可用的 capsule（不是 `TBD` 空模板）
- 直接生成一批默认 research agent brief（可用 `--preset none` 关闭）

**最小共享上下文**：
- `tasks/.../capsules/task-capsule.md`
- `tasks/.../capsules/skill-brief.md`
- `tasks/.../agents/<agent>.md`

**并发规则**：
- 并发 agent 只读 capsule + 自己的 brief，不重放整段调研历史
- 原始资料放 `tasks/.../sources/`
- 量化 scratch、CSV、临时脚本放 `tasks/.../scratch/`
- 研究中间稿放 `tasks/.../research/` 或 `tasks/.../reports/`
- task-local draft 先保留在 `tasks/.../reports/`
- 正式报告再通过 `handoff-artifact.sh` 复制归档到 `workspace/report/`
- `info-collector-*` / 独立量化校验可以先并发；`deep-analyst` / `history-analyst` / `synthesis-analyst` / `report-generator` 这类下游 lane 默认要等上游证据落盘后再启动或重跑
- 如果下游 lane 被提前拉起，必须显式记成 `waiting`，并把缺失的 upstream artifact 写清楚；不能一边等待一边对外宣称“已经在深度分析”
- 主 agent 每次汇报进度前，都应先看 task-local orchestration；若存在 `ready_to_launch` 或 `ready_to_resume`，先继续调度，不要把“干等”转嫁给用户

**批量准备默认 agent**：

```bash
bash workspace/scripts/skill-prepare-batch.sh deep-research default "" "<task-slug>"
```

如果任务涉及金融市场、选股、财报、新闻、行情、期权或其他高时效交易 intelligence，额外读取：

- `references/finance-timeliness-playbook.md`

并把 `Data Freshness & Completeness` 与 `Precision level` 当成硬合同，而不是建议项。

`deep-research` 的 `report-generator` 默认输出语言现在应为：

- `Simplified Chinese (zh-CN)`

只有当用户明确要求英文时，才切换到英文。

---

## 核心理念

### 学术报告级引用管理

**引用标记规范**：
- **文中引用**：使用 `[数字]` 形式标记引用位置（像正经学术报告）
- **Reference Section**：在报告最后添加专门的引用部分
- **引用格式**：`[数字] [标题] ([来源], [时间])` - 链接格式
- **引用列表**：按顺序列出所有引用的新闻/文章链接

**示例**：
```markdown
研究发现：美伊冲突导致全球市场波动 [1] [2] [3]

其中，美国对伊朗的制裁措施已实施多年，形成了完整的贸易封锁网络 [4] [5] [6]。
```

**关键论据来源硬化规则**：
- 如果一个论据直接支撑：
  - 政策判断
  - 动机归因
  - 决策链
  - 结论强度
  - 核心数字口径
  那么默认不能只停在聚合页、博客、自媒体或二手转述。
- `知乎专栏 / CSDN / 腾讯聚合页 / 微信公众号 / 博客` 可以作为线索入口，但不应作为最关键论据的最终落脚点，除非用户明确接受次级来源。
- 对这类线索型来源，默认动作应是继续追到：
  - 官方原文
  - 官方 PDF / 政策正文
  - 政府官网 / 医院官网
  - 同行评审论文
  - 权威机构正式发布
- 如果暂时找不到原始来源，报告里必须明确标注“该证据层级较弱”或“该表述基于二手转述”，不能直接写成“官方已明确”。

**引用可核查底线**：
- 无论是主 agent 还是子 agent，只要输出的是 deep-research 报告或 task-local 研究稿，就必须把实际查到的来源链接补齐。
- `references / citations / sources` 中不允许留下只有标题、只有 PMID/DOI、只有来源名、或 `https://...` / `TBD` / `待补` 这类占位值的条目。
- 如果条目已经包含 `DOI / PMID / PMCID`，workspace 会在落盘前尝试自动归一化成官方链接，但这只补“已有标识符”的学术条目，不会替你额外搜索普通网页来源。
- 如果暂时只有线索但没有可点击 URL，这类内容只能放到：
  - `Unverified Leads`
  - `Limitations`
  - `待进一步核查`
  不能继续留在 `参考文献` 或正式引用载荷里。
- 自动补链命令：

```bash
python3 workspace/scripts/deep_research_reference_normalizer.py --report <report-path> --in-place
```

- workspace 内的硬校验命令：

```bash
python3 workspace/scripts/deep_research_reference_guard.py --report <report-path>
```

- 最终正式交付前，统一走：

```bash
bash workspace/scripts/deep-research-deliver.sh --path <report-path>
```

**分层赋权规则**：
- 这不是“强信源替代弱信源”的非此即彼关系，而是“强弱信源并存、但结论权重分层”。
- 强信源负责锚定：
  - 政策文本
  - 硬数字
  - 正式制度
  - 明确表态
  - 决策链主干
- 弱信源可以保留，用于补充：
  - 潜规则
  - 非正式激励
  - 科室内部操作习惯
  - 一线抱怨与博弈细节
  - 需要进一步验证的行业传闻
- 写作时必须区分：
  - `高权重结论`
  - `中权重支持`
  - `低权重软信号`
- 当弱信源与强信源冲突时，强信源决定事实口径；弱信源只保留为“存在这种说法/实践线索”。

### 文件发送能力

**文件发送机制**：
- **Markdown 报告文件**：调研结束后自动生成并保存到 `workspace/report/[主题]_[时间戳].md`
- **飞书文件发送**：除了文字消息外，自动将 Markdown 文件发送给用户
- **文件命名规范**：`[主题]_[时间戳].md`
- **存储位置**：`workspace/report/` 目录

### 轻量量化验证能力

当研究问题涉及利率、增长率、估值、样本对比、趋势判断、简单预测或“算一下是否成立”时，本 skill 允许 agent 在容器内部执行轻量脚本验证。

**设计原则**：
- 优先使用标准库和当前容器已有能力
- 允许编写临时脚本，但脚本必须服务于当前研究问题
- 优先做简单、可解释、可复核的线性建模与公式校验
- 结论必须把数据来源、样本量、方法和局限性写回报告

**现成脚本工具**：
- `workspace/skills/deep-research/scripts/research_quant_toolkit.py`
- `workspace/skills/deep-research/scripts/quant_scratchpad_template.py`
- `workspace/skills/deep-research/references/quant-research-playbook.md`

## 金融高时效任务附加规则

当任务是：

- 市场研究
- 选股 / 选行业 / 选合约
- 财报 / 新闻 / 行情 / 技术面 / 资金面
- 真实交易方向判断

必须额外遵守：

1. 最新市场状态优先于旧新闻叙事。
2. 历史信息必须串成 timeline，不能直接当成当前状态。
3. 若关键最新数据缺失，必须降级为：
   - `DIRECTIONAL_ONLY`
   - `WATCHLIST`
   - `NOT_EXECUTABLE`
4. 没有真实期权链，不得给 precise strike / expiry / IV judgement。
5. 模板 quant 输入不得参与真实交易结论。
6. 若 mixed freshness 风险不是 `LOW`，或 timeline integrity 不是 `COHERENT`，则不得输出 `EXECUTABLE`。
7. 新闻、财报、政策、地缘政治等事件必须结构化落盘，并在最终报告中体现为 `事件驱动因子`，不能只藏在 worklog。

---

## Agent 体系

### Agent 类型定义（与 v2.1.0 相同）

#### 1. Info Collector (信息收集员)
**职责**：系统性地从多个来源快速收集原始信息
**输出**：结构化的信息收集结果，包含来源链接和引用标记

#### 2. Deep Analyst (深度分析师)
**职责**：基于 Info Collector 的结果进行多维度分析
**输出**：结构化的分析报告，包含引用标记

#### 3. Technical Feasibility Analyst (技术可行性分析师)
**职责**：从技术和经济角度分析可行性
**输出**：技术可行性评估报告，包含引用标记

#### 4. History Analyst (历史分析师)
**职责**：重构历史事件，分析因果关系链
**输出**：历史分析报告，包含引用标记

#### 5. Synthesis Analyst (综合分析师)
**职责**：综合所有 Agent 的研究结果，生成带引用的最终报告
**输出**：带引用标记的综合分析报告

#### 6. Report Generator (报告生成器)
**职责**：生成标准化报告，包含完整的 Reference Section，并发送文件
**输出**：Markdown 报告文件 + 飞书文件发送

#### 7. Quant Verifier (量化验证员)
**职责**：在研究涉及数字、时间序列、估值、利率、增长率、财务比率、趋势判断时，执行轻量数据抓取、描述统计、简单线性回归和公式校验
**输出**：可复核的数值结论、脚本输出摘要、方法局限性说明

---

## 引用管理机制

### 引用标记规范

#### 文中引用格式
- **标准格式**：`[数字]` - 数字从 1 开始递增
- **使用场景**：在正文中需要引用来源时标记

**示例**：
```markdown
研究发现：美伊冲突对全球市场产生了显著影响 [1] [2]。

美国对伊朗的制裁措施已实施多年 [3] [4]，形成了完整的贸易封锁网络 [5]。

这种制裁机制依赖于高度情报协同、数据共享和全球金融市场的"合规外包" [6] [7]。
```

#### Reference Section 格式

**标准格式**：
```markdown
---

## 参考文献 (References)

### 1. [标题 1]
**来源**: [来源名称]
**时间**: [发布时间]
**链接**: [URL]

### 2. [标题 2]
**来源**: [来源名称]
**时间**: [发布时间]
**链接**: [URL]

### ...
```

**示例**：
```markdown
---

## 参考文献 (References)

### 1. 美以伊冲突最新解读：对全球市场影响有多大？
**来源**: BNY 投资
**时间**: 2026-03-05
**链接**: https://www.bny.com/investments/hk/zh-cn/institutional/news-and-insights/articles/iran-conflict-market-implications-asian.html

### 2. 美以袭击伊朗 全球市场波动加剧
**来源**: 新华网
**时间**: 2026-03-02
**链接**: https://www.news.cn/world/20260302/e0ec8c3a323c42f3929ce8cad321882a/c.html

### 3. 中金：美伊冲突演绎及对FICC资产影响分析
**来源**: 富邦证券
**时间**: 2026-03-02
**链接**: https://www.fubon.com/banking/document/Corporate/Financial_Market/TW/%E5%B8%82%E5%A0%B4%E8%BD%89%E6%8A%98%E7%84%A6%E9%BB%9E_20260302.pdf

### 4. 美国对伊朗实施新一轮制裁
**来源**: 央视新闻
**时间**: 2026-01-23
**链接**: https://www.stcn.com/article/detail/3610308.html

### 5. 美国"二级制裁"铁幕下，伊朗石油如何"暗度陈仓"？
**来源**: 澎湃新闻
**时间**: 未注明
**链接**: https://m.thepaper.cn/newsDetail_forward_31987017

### 6. 制裁与伊朗石油相关的实体和船只
**来源**: 中国驻美国大使馆官网
**时间**: 2025-04-11
**链接**: https://china.usembassy-china.org.cn/sanctions-on-irans-oil-network-to-further-impose-maximum-pressure-on-iran

### 7. 制裁与伊朗石油相关的实体和船只
**来源**: 中国驻美国大使馆官网
**时间**: 2025-03-21
**链接**: https://china.usembassy-china.org.cn/sanctioning-additional-entities-that-have-traded-in-irans-petroleum
```

---

## 报告生成流程

### 阶段 0: 量化触发判断（新增）

当用户问题出现以下任一信号时，先判断是否应启用 Quant Verifier：

- 明确出现数据、比率、涨跌幅、估值、利率、收益率、通胀、失业率、相关性、趋势、回归、预测
- 用户要求“算一下”“估算一下”“建个简单模型”“用数据验证”
- 研究对象本身高度依赖时间序列或财务/宏观数字

**启用后必须做的事**：
1. 明确变量、时间范围、数据来源
2. 判断只需要公式核算、描述统计，还是需要简单线性回归
3. 优先使用现成脚本；仅在必要时写临时 scratch 脚本
4. 把数值验证结果写回报告，而不是只说“脚本跑过了”

### 阶段 1: 信息收集（带引用标记）

**Agent A (Info Collector)** 任务：
1. 从多个源搜索信息
2. 记录来源 URL 和发布时间
3. 生成带 `[数字]` 引用标记的初步报告
4. 确保每个事实都有对应的引用标记
5. 如果某条线索还没有直接 URL，不得把它放进 `citations` / `references`，只能放进 `unverified_leads`
6. 如果已有 `DOI / PMID / PMCID`，在落盘前先用 normalizer 自动补官方 URL

**输出格式**：
```json
{
  "findings": [
    {
      "fact": "事实描述",
      "sources": [
        {
          "title": "文章标题",
          "url": "https://...",
          "date": "2026-03-10",
          "reliability": "high"
        }
      ]
    }
  ],
  "citations": [
    {
      "id": 1,
      "title": "文章标题",
      "url": "https://...",
      "date": "2026-03-10"
    }
  ],
  "unverified_leads": [
    {
      "claim": "只有标题或 DOI，还没补到实际 URL 的线索",
      "reason": "缺少可核查链接，不能进入 references"
    }
  ]
}
```

---

### 阶段 2: 深度分析（集成引用）

**Agent B (Deep Analyst)** 任务：
1. 对收集的信息进行多维度分析
2. 在分析结果中引用具体来源
3. 使用 `[数字]` 引用标记
4. 不得把无 URL 的二手线索继续抬升为正式引用

**输出格式**：
```json
{
  "analysis": {
    "source_reliability": "high",
    "evidence_sufficiency": "sufficient",
    "contradictions": [],
    "technical_feasibility": "high"
  },
  "citations_used": [1, 2, 3, 4, 5, 6, 7]
}
```

---

### 阶段 2.5: 量化验证（新增）

**Quant Verifier** 任务：
1. 从官方公开来源或研究数据表中抽取结构化数字
2. 优先在当前 task 目录的 `scratch/` 中保存临时 CSV / 临时脚本；没有活动 task 时再退回 `workspace/report/_scratch/`
3. 使用轻量工具完成描述统计、简单回归或公式核算
4. 产出“数据来源 + 方法 + 结果 + 局限性”的验证结论

**默认工作目录**：
- 优先：`workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/`
- 回退：`workspace/report/_scratch/`

**可直接使用的命令**：

```bash
# 1) 抓取 FRED 历史利率数据
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py fetch-fred \
  --series FEDFUNDS \
  --start 2015-01-01 \
  --output workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/fedfunds.csv

# 2) 对某一列做描述统计
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py describe \
  --input workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/fedfunds.csv \
  --column value

# 3) 对清洗过的 CSV 做简单线性回归 y ~ x
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py regress \
  --input workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/model_input.csv \
  --x fedfunds \
  --y inflation \
  --json

# 4) 快速核算一个公式
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py calc \
  --expr "(new-old)/old*100" \
  --var old=5.25 \
  --var new=4.50
```

**写 scratch 脚本的规则**：
- 仅在标准命令不够用时才写临时脚本
- 临时脚本命名建议：`workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/YYYY-MM-DD-<topic>-analysis.py`
- 优先从 `quant_scratchpad_template.py` 复制后最小改动
- 任务结束时，保留有价值的脚本，删除纯垃圾实验脚本

**当前环境假设**：
- 默认可用：Python 标准库 + `requests`
- 不默认依赖：`numpy`、`pandas`、`statsmodels`
- 因此优先做简单可解释的模型；如果需要额外包，必须在报告中说明环境依赖与不确定性

---

### 阶段 3: 报告生成（含完整 Reference Section）

**Agent F (Report Generator)** 任务：
1. 整合所有 Agent 的结果
2. 生成带 `[数字]` 引用标记的正文
3. 生成完整的 Reference Section
4. 如果是金融高时效任务，固定增加 `## Data Freshness & Completeness`
5. 在任何正式交付前，先运行：
   - `python3 workspace/scripts/deep_research_reference_normalizer.py --report <report> --in-place`
6. 再运行：
   - `python3 workspace/scripts/deep_research_reference_guard.py --report <report>`
7. 金融高时效任务在交付前再运行：
   - `python3 workspace/scripts/finance-intel-report-gate.py --report <report> --task-slug <slug>`
8. 先保存 task-local draft 到 `tasks/.../reports/<task-slug>-draft.md`
9. 统一优先运行 `workspace/scripts/deep-research-deliver.sh --path <report>`；该脚本会先做 DOI/PMID/PMCID 自动补链，再做 reference guard，再按需做 finance gate，并把最终交付复制到 `workspace/report/`
10. 优先通过消息工具的 `filePath` 参数发送；如果当前回合只能输出文本，则至少原样输出 `FILEPATH:./...`
11. 最终回复应同时带上 `TASK_PATH:./tasks/...`

**报告结构**：
```markdown
# [研究主题] - 深度调研报告

**报告编号**: [自动编号]
**生成时间**: [ISO 8601 格式]
**研究复杂度**: [简单/中等/复杂]

---

## 执行摘要

**研究目标**:
- [目标 1]
- [目标 2]

**主要发现**:
- [关键事实 1]
- [关键事实 2]

**结论（1-3 句话）**:
- [结论]

**可信度评估**: [高/中/低]

---

## Data Freshness & Completeness

- Market data as of:
- News data as of:
- Options data as of:
- Options data status:
- Timeline span:
- Completeness status:
- Precision level:
- Critical missing fields:
- Fallback sources used:
- Mixed freshness risk:
- Timeline integrity:
- Open interest status:
- Bid-ask status:
- Expiry-window fit:

---

## 研究方法

### 信息源
- 列出所有信息源及其可靠性评估

### 搜索策略
- 搜索关键词
- 信息源选择理由
- 对 `info-collector-*`，优先使用 `workspace/skills/deep-research/scripts/info_search_scheduler.py`
- 该脚本负责最小可执行的 MCP-first 调度：优先学术/专用 MCP，再退到通用网页搜索
- 当 `Brave` 出现 `429` / `quota` / `rate limit` 时，不要反复重试；用脚本把 Brave family 标记为 cooling，然后切换到下一个 lane
- 对任何不熟悉的 MCP server，先执行 `mcp_call(action=list_tools, server=...)`，再做正式 `call`

---

## 核心发现

### 确定的事实（经过验证，带引用）
- 事实 1:
  - 证据: [来源] [1] [2]
  - 可靠性: [高/中/低]
  - 引用: [来源链接]

- 事实 2:
  - 证据: [来源] [3] [4]
  - 可靠性: [高/中/低]
  - 引用: [来源链接]

### 存在争议（带引用）
- 争议点 1:
  - 支持观点 A 的证据: [来源] [5] [6]
  - 支持观点 B 的证据: [来源] [7]
  - 中立分析: [来源] [8]

### 技术/科学原理（带引用）
- 原理说明: [来源] [9] [10]
- 学术共识: [来源] [11]
- 技术可行性评估: [来源] [12]

---

## 深度分析

### 因果分析（带引用）
- 前因: [原因] [引用来源]
- 后果: [结果] [引用来源]
- 间接影响: [影响] [引用来源]

### 跨领域视角（带引用）
- 技术视角: [分析] [引用来源]
- 经济视角: [分析] [引用来源]
- 社会/政策视角: [分析] [引用来源]
- 历史/文化视角: [分析] [引用来源]

---

## 结论与建议

### 主要结论
- 重新总结核心发现（带引用）

### 建议
- 基于研究的建议（带引用）

### 后续研究方向
- 尚未解决的问题（带引用）

---

## 参考文献 (References)

### 1. [标题 1]
**来源**: [来源名称]
**时间**: [发布时间]
**链接**: [URL]

### 2. [标题 2]
**来源**: [来源名称]
**时间**: [发布时间]
**链接**: [URL]

### ... (列出所有引用)

## 未核查线索（可选）

- 只保留暂时没有补齐 URL 的线索
- 明确写清为什么还不能纳入正式参考文献
- 这一节不能参与正式 `[数字]` 引用编号

---

## 附件
- [相关文档、数据截图等]

---

*本报告由 Deep Research Skill 自动生成*
```

---

## 文件发送机制

### 文件生成

**命名规范**：
- 格式：`[主题]_[时间戳].md`
- 时间戳格式：`YYYY-MM-DD-HH-MM` (ISO 8601 标准)
- 命名规则：使用英文主题（避免文件名编码问题）

**存储路径**：
- 自动保存到：`workspace/report/[主题]_[时间戳].md`

**示例**：
```
iran_stock_market_impact_2026-03-10-17-30.md
petroleum_reservoir_feasibility_2026-03-10-15-30.md
```

---

### 飞书文件发送 / 聊天文件交付

**发送触发**：
- 调研任务完成后自动发送
- 用户也可以手动触发：`"发送报告 [文件名]"`

**发送流程**：
1. 检查文件是否存在于 `workspace/report/`
2. 执行：

```bash
bash workspace/scripts/deep-research-deliver.sh --path workspace/report/<file>.md
```

3. 该脚本会先尝试把 DOI / PMID / PMCID 归一化成官方链接，再拦截仍然缺链接的 reference，并按需执行 finance gate
4. 如果有消息工具可用，则把返回的相对路径作为 `filePath` 发送
5. 如果当前只能返回文本，则至少单独输出一行：

```text
FILEPATH:./report/<file>.md
```

6. 不要只回复“文件路径: ./report/...”，这不是稳定的文件交付格式

**发送消息模板**：
```markdown
## 📄 深度调研报告已生成

**文件名**: [文件名]
**存储位置**: workspace/report/
**生成时间**: [ISO 8601 格式]

**内容摘要**:
- 主要发现: [1-2 句话]
- 结论: [1-2 句话]
- 可信度: [高/中/低]

**文件已发送**，请查收！
```

**强制交付规则**：
- 生成正式报告后，不要停在“路径提示”
- 必须走 `deep-research-deliver.sh` 或等价的 `filePath` 发送动作
- `deep-research-deliver.sh` 会拒绝 reference 中缺少真实链接的报告
- 当用户明确说“把报告发给我”时，优先发文件，不要改成长篇摘要代替文件

---

## 使用指南

### 何时使用本 skill

**推荐使用场景**：
- 🔬 技术可行性深度分析（如"XX 技术是否可行"）→ 并行模式 + 文件发送
- 📰 科学谣言验证（如"XX 技术突破"是否真实）→ 并行模式 + 文件发送
- 🏭️ 历史事件调查（如"XX 事件的真相"）→ 流水线模式 + 文件发送
- 💼 投资决策支持（如"XX 项目是否值得投资"）→ 并行模式 + 文件发送
- 📚 学术研究支持（如"XX 领域的研究现状"）→ 流水线模式 + 文件发送

### 新增功能

#### 引用管理
- ✅ **文中引用标记**：使用 `[数字]` 格式
- ✅ **Reference Section**：在报告最后添加完整的引用列表
- ✅ **学术报告级格式**：像正经学术报告一样

#### 文件发送
- ✅ **自动文件发送**：调研结束后自动发送 Markdown 文件
- ✅ **手动文件发送**：用户可以通过指令手动触发
- ✅ **文件命名规范**：`[主题]_[时间戳].md`
- ✅ **存储位置标准化**：`workspace/report/`

#### 量化验证
- ✅ **轻量数据抓取**：支持 FRED 等固定公开时间序列
- ✅ **轻量描述统计**：均值、中位数、波动、极值
- ✅ **简单线性回归**：单变量线性关系快速验证
- ✅ **公式核算**：对关键百分比、增长率、利差等做计算复核
- ✅ **临时脚本模板**：支持在研究任务中快速搭建 scratch 分析

---

## 质量标准

### 报告质量
- ✅ 引用标记准确：每个引用都有明确的 `[数字]` 标记
- ✅ Reference Section 完整：包含所有引用的标题、来源、时间、链接
- ✅ 引用规范统一：所有引用使用相同格式
- ✅ 交叉引用正确：正文中的 `[数字]` 与 Reference Section 中的编号对应

### 文件管理
- ✅ 文件命名规范：`[主题]_[时间戳].md`
- ✅ 存储位置统一：`workspace/report/`
- ✅ 文件发送确认：发送后生成确认消息

### 研究质量
- ✅ 多源验证（每个事实用 3 个以上来源验证）
- ✅ 深度分析覆盖（6 个维度全覆盖）
- ✅ 矛盾识别准确率 > 90%
- ✅ 交叉验证执行率 100%
- ✅ 涉及核心数字结论时，必须至少执行一次公式核算、描述统计或简单回归验证
- ✅ 量化验证结论必须包含数据来源、样本量、方法和局限性

---

## 实际使用示例

### 示例 1: 伊朗地区局势对美股市场影响研究

**研究主题**：伊朗地区局势对美股市场影响
**执行模式**：并行模式（4 个 Agent 同时工作）
**引用管理**：启用文中 `[数字]` 引用标记 + Reference Section
**文件发送**：启用自动文件发送

**执行流程**：
1. **信息收集**：4 个 Agent 并行搜索，记录所有来源链接
2. **深度分析**：对收集的信息进行多维度分析，添加引用标记
3. **报告生成**：生成带 `[数字]` 引用标记的正文 + 完整 Reference Section
4. **文件保存**：保存到 `workspace/report/iran_stock_market_impact_2026-03-10-17-30.md`
5. **文件发送**：自动发送 Markdown 文件给用户

**用户接收**：
- 📊 文字消息：包含研究摘要和主要发现
- 📄 飞书文件：完整的 Markdown 报告（含 Reference Section）

---

*本 skill 基于完全内置的多 Agent 并行架构设计，支持引用管理、文件发送、轻量量化验证和实时进度反馈。版本 2.3.0*
