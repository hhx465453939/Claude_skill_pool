---
name: geo-sentinel
description: "LLM-powered geopolitical and macro news forecasting system with task-container-first F-G+ calibration. Predicts event trajectories using multi-round intelligence gathering plus a lightweight mathematical constraint layer anchored on base rates, decomposition, counter-evidence, and prior-aware recalibration. Trigger when user asks to predict, forecast, or analyze future developments of geopolitical events, wars, elections, policy shifts, market-moving news, regime changes, trade disputes, sanctions, diplomatic crises, or any current-affairs scenario where what happens next is the core question. Not for: historical analysis without forward prediction, pure opinion polling. Keywords: 预测 走向 接下来 会怎样 forecast predict scenario 态势 推演 局势."
---

# Geo Sentinel — News Forecasting with F-G+ Constraint

## Overview

Geo Sentinel 是一个 task-container-first 的预测流水线。它保留原来的 F-G 双函数精神，但把约束层升级为 `F-G+`：

- `F`: 多场景自然语言推理
- `G`: 基准率锚定、驱动拆解、反证校准、先验感知再校准、轻量不确定性边界

核心流程：

```text
task 容器启动
  → 多轮情报搜索（shared wrapper + SEARCH_RUNTIME）
  → reference class / driver decomposition
  → F(场景生成 + 可选 inner-crowd)
  → G(基准率与先验感知校准)
  → task 内落盘
  → 报告 + Feishu Delivery
```

## Phase 0 — Task Container Bootstrapping

复杂预测任务必须先进入 task 容器。推荐命令：

- `bash workspace/scripts/code-debugger-task-bootstrap.sh "<task-slug>" "<title>" "geo-sentinel-forecast"`

至少需要以下 task-local 目录：

- `input/raw/`
- `input/normalized/`
- `sources/raw/`
- `sources/digests/`
- `scripts/`
- `scratch/`
- `results/`
- `reports/`
- `handoff/`

所有输入情报、搜索回包、计算脚本、计算结果、预测报告都必须只留在当前 task 内，不要外溢到 `workspace/report/`、`workspace/memory/` 或仓库根目录。

## Phase 1 — Intelligence Collection (情报采集)

### 1.1 搜索运行时硬约束

- `Load SEARCH_RUNTIME.md before any search step.`
- 情报搜索必须服从 `./SEARCH_RUNTIME.md` 以及 gateway wrapper 的共享交规。
- 第一个可执行搜索动作必须是 shared wrapper first，而不是 skill 自己绕过 runtime 指定 provider。
- 对泛化网页 / 时效情报 / 地缘与热点话题，默认第一跳应由 runtime 落到 `open-websearch`；后续是否升级到 `zhipu`、`metaso`、`tavily`、`brave`，由 wrapper 和 gateway guard 决定。
- 不要直接以原生 Brave-backed `web_search` 作为起手动作；这在当前 runtime 下属于 routing violation。
- 每轮搜索都必须把 raw capture 落到 `sources/raw/`，把 digest 落到 `sources/digests/`，并记下真实使用的 lane / provider。

### 1.2 搜索强度硬约束

- 基础预测任务：至少 `3-5` 轮具有关联扩词的关键词检索组。
- 重大预测任务：至少 `5-10` 轮具有关联扩词的关键词检索组。

每轮检索都要覆盖至少以下一个维度，且轮次之间必须有扩词或约束递进：

1. 核心事件主词
2. 关键 actor / 主体
3. 反向论点 / counter-evidence
4. 历史类比 / reference class
5. 触发条件 / 时间窗口
6. 二级影响 / 市场传导

### 1.3 每轮检索落盘要求

每轮结束时至少落盘：

- `sources/raw/round-XX-search.md`
- `sources/digests/round-XX-digest.md`

digest 至少包含：

- 当前主叙事
- 本轮新增事实
- 本轮反证
- 关键未知量
- 下一轮扩词计划

### 1.4 结构化情报包

完成搜索后，整理为 task-local `intel_packet`，推荐路径：

- `input/normalized/intel-packet.json`

建议包含字段：

```json
{
  "topic": "...",
  "time_horizon_days": 30,
  "timeline": [],
  "actors": [],
  "constraints": [],
  "signals": {
    "supporting": [],
    "contradicting": []
  },
  "historical": {
    "event_category": "diplomatic_negotiations",
    "base_rate": 0.24,
    "reference_class_size": 12
  },
  "scenarios": [
    {
      "id": "S1",
      "title": "...",
      "llm_probability": 0.42,
      "base_rate": 0.25,
      "supporting_signals": [],
      "contradicting_signals": [],
      "analogues": []
    }
  ]
}
```

## Phase 2 — F-G+ Forecasting

`F-G+` 不是完全抛弃双函数，而是对旧版做低成本升级。

### F — 场景生成

Agent 必须：

- 生成多个互斥或近互斥场景，而不是单一路径
- 先做 outside view，再做 inside view
- 明确关键驱动、关键抑制因素、触发条件、失效条件

若 token 允许，推荐做一个低成本 inner-crowd：

- `reference-class view`
- `actor / incentive view`
- `contrarian view`

把多个概率估计写入 `llm_probabilities`，交给约束引擎聚合。

### G — 约束与校准

约束层默认执行以下几步：

1. `Base-rate anchor`
   - 先用 reference class 给每个场景一个基准率锚点。
2. `Decomposition-recomposition`
   - 把结论拆到驱动层，再回组合成场景概率。
3. `Counter-evidence discipline`
   - 反证不再只写在 prose 里，而要进入概率校准。
4. `Prior-aware recalibration`
   - 以 reference class 或估计先验为锚，而不是机械地围绕 `0.5` 做极值化。
5. `Tail discipline`
   - 极端低基准率情景若证据不够强，不允许被随意拉到高概率。

## Phase 3 — Constraint Engine

运行 Python 约束引擎：

- `python3 scripts/forecast_engine.py --input INPUT.json --output OUTPUT.json`

推荐 task-local 路径：

- 输入：`input/normalized/intel-packet.json`
- 输出：`results/forecast-engine.json`

引擎输出示例：

```json
{
  "topic": "...",
  "analysis_date": "2026-04-07T00:00:00Z",
  "time_horizon_days": 30,
  "scenarios": [
    {
      "id": "S1",
      "title": "...",
      "probability": 0.43,
      "ci_lower": 0.31,
      "ci_upper": 0.55,
      "drivers": [],
      "disruptors": [],
      "watch_signals": [],
      "calibration": {
        "base_rate": 0.25,
        "anchor": 0.25,
        "llm_center": 0.41,
        "llm_dispersion": 0.06,
        "signal_score": 0.33,
        "analogue_score": 0.21,
        "gamma": 1.08
      }
    }
  ],
  "iterations": 2,
  "convergence": true,
  "confidence_level": "moderate"
}
```

## Phase 4 — Report Generation

最终报告必须落在 task 内，推荐路径：

- `reports/<task-slug>-forecast.md`

最少包含以下章节：

1. `Executive Summary`
2. `Scenario Tree`
3. `Key Drivers & Counter-Drivers`
4. `Watch Indicators`
5. `Calibration Notes`
6. `Search Coverage & Gaps`
7. `Feishu Delivery`

`Feishu Delivery` 必须显式包含：

- `REPORT_PATH: ./tasks/.../reports/...`
- `TASK_PATH: ./tasks/...`
- `COPY_SOURCE: 从 REPORT_PATH 或 deliver-report.sh 返回的 FILEPATH 复制后发送给飞书用户`

正式交付前，优先执行：

- `bash workspace/scripts/deliver-report.sh --path "<task-dir>/reports/<final-report>.md"`

并把输出存到：

- `handoff/delivery.txt`

## Mathematical Model Reference

约束模型的公式和参数见：

- `references/constraint-model.md`

## Tool Usage

- Search:
  - 先走 shared wrapper，再遵守 `SEARCH_RUNTIME.md`
- Forecast engine:
  - `python3 scripts/forecast_engine.py --input INPUT.json --output OUTPUT.json`
- Delivery:
  - `bash workspace/scripts/deliver-report.sh --path "<task-dir>/reports/<final-report>.md"`

## Important Notes

- 报告主体语言必须使用中文书写。
- 永远给出多个场景，不给单一决定论结论。
- 时间敏感预测必须标注分析日期和预测窗口。
- 没有可靠 reference class 时，要主动降低置信度并放宽区间。
- 预测报告必须把“基准率”“当前证据”“反证”“引擎再校准”分开写，避免把不同层级的判断混成一句话。
