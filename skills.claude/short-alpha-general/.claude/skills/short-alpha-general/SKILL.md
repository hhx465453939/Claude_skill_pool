---
name: short-alpha-general
description: 短周期战役型交易将军技能。目标是在不完美数据条件下，围绕道天地将法与容量梯度策略池，持续输出 4小时-20个交易日的高质量单名股机会。
---

# Short Alpha General

这是一个新的战役型短周期交易技能骨架。

当前阶段先以生产级技术规范为主，源文件见：

- `workspace/.debug/short-alpha-general-build/SPEC.md`

## 定位

- `market-alpha-orchestrator` 是朝廷与帅：负责调度、后勤、数据层、交付
- `short-alpha-general` 是将：负责短周期庙算、OODA 战争循环、战场选择、容量部署、执行判定

## 当前状态

- 规格已建立
- 已有 bootstrap、observe/doctrine engines、capacity pool、review gate、OODA、report packager、runtime guard 与 smoke 流程

## 默认协作关系

- 需要顶层战略框架时，联动 `executive-consultant`
- 需要复杂多线战役设计时，联动 `superpowers`
- 需要重检索 / 重证据 / 重引用时，联动 `deep-research`
- 需要现有市场研究编排与交付时，联动 `market-alpha-orchestrator`

## 常用命令

### Bootstrap

```bash
bash workspace/skills/short-alpha-general/scripts/short-alpha-general-bootstrap.sh \
  --task-slug "short-alpha-general-us-smoke" \
  --market us \
  --horizon w1-4 \
  --objective "build a short-horizon battle plan"
```

### Full Smoke

```bash
bash workspace/skills/short-alpha-general/scripts/short-alpha-general-smoke.sh
```

### Battle Runner

```bash
python3 workspace/skills/short-alpha-general/scripts/short-alpha-battle-runner.py \
  --task-slug "<task-slug>" \
  --raw-candidates "<task>/results/candidates/candidates.json" \
  --news-log "<task>/sources/news-event-log.jsonl" \
  --truth-ledger "<task>/reports/derivatives/underlying-truth-ledger.json" \
  --degrade-reason "provider_rate_limit"
```

### 核心引擎

```bash
python3 workspace/skills/short-alpha-general/scripts/short-alpha-regime-engine.py --task-slug "<task-slug>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-event-clock.py --task-slug "<task-slug>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-terrain-engine.py --task-slug "<task-slug>" --candidates-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-fertility-engine.py --task-slug "<task-slug>" --candidates-input "<path>" --terrain-input "<path>" --event-clock-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-campaign-score.py --task-slug "<task-slug>" --candidates-input "<path>" --regime-input "<path>" --terrain-input "<path>" --fertility-input "<path>" --event-clock-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-execution-governor.py --task-slug "<task-slug>" --campaign-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-capacity-pool.py --task-slug "<task-slug>" --campaign-input "<path>" --execution-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-review-gate.py --task-slug "<task-slug>" --regime-input "<path>" --campaign-input "<path>" --execution-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-ooda-loop.py --task-slug "<task-slug>" --regime-input "<path>" --event-clock-input "<path>" --fertility-input "<path>" --execution-input "<path>" --review-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-strategy-register.py --task-slug "<task-slug>" --campaign-input "<path>" --execution-input "<path>" --review-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-score-calibration.py --task-slug "<task-slug>" --campaign-input "<path>" --execution-input "<path>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-report-packager.py --task-slug "<task-slug>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-runtime-guard.py status --task-slug "<task-slug>"
python3 workspace/skills/short-alpha-general/scripts/short-alpha-battle-runner.py --task-slug "<task-slug>" --raw-candidates "<path>" --news-log "<path>" --truth-ledger "<path>"
```

## Runtime Discipline

- 当前真实任务中，严禁直接读取历史 smoke task 路径。
- 当前 task 由 bootstrap 创建后，唯一合法状态文件是当前 task 的 `TASK_ORCHESTRATION.md`。
- 当前 skill 的搜索交规必须硬读取并服从：
  - `workspace/SEARCH_RUNTIME.md`
- 对 finance/macro/market 问题：
  - `finance-mcp -> open-websearch -> zhipu -> metaso -> tavily -> brave`
- 对一般网页与实时市场情报：
  - 第一个可执行搜索动作必须优先 `open-websearch`
- 不允许把 Brave-backed 原生 `web_search` 当成默认起手动作。
- 如果模型供应商限速或 timeout：
  - 自动并发梯度：`6 -> 4 -> 2 -> 1`
  - 仍失败则切换 `parent-only`
  - 主 agent 必须继续单线程把任务推下去，不能停在半空。
- 推荐动作：
  - 先运行 `python3 workspace/skills/short-alpha-general/scripts/short-alpha-runtime-guard.py status --task-slug "<task-slug>"`
  - 若遇到 rate limit / timeout：
    - `python3 workspace/skills/short-alpha-general/scripts/short-alpha-runtime-guard.py degrade --task-slug "<task-slug>" --reason "rate_limit"`
  - 若已经降到 `1` 仍失败：
    - `python3 workspace/skills/short-alpha-general/scripts/short-alpha-runtime-guard.py parent-only --task-slug "<task-slug>" --reason "provider_rate_limit"`
  - 然后继续由主 agent 单线程串行推进，不允许把任务留在未完成状态。

## 真实任务硬规则

- 真实用户请求必须创建新的 task 容器，不得复用任何 `short-alpha-general-smoke` / `short-alpha-general-us-smoke` 路径。
- 真实运行时，若 task 内已有：
  - `results/candidates/candidates.json`
  - `sources/news-event-log.jsonl`
  必须先跑 `short-alpha-market-observe.py`，再跑后续引擎。
- 不允许在 `review-gate` 返回 `REVIEW_FAIL` 后直接手写最终报告来绕过流水线；必须先修 Observe / campaign / execution 链。
- 若搜索升级到 `tavily` / `brave`，必须有明确理由：
  - 低成本 lane 失败
  - 低成本 lane 信息不足
  - 或当前 task 明确允许 premium escalation
