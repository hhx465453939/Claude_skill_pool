# Finance Timeliness Playbook

这个参考件只在以下任务中启用：

- 金融市场
- 选股 / 选行业 / 选合约
- 财报、新闻、行情、技术面、资金面
- 任何会影响真实交易方向的时效性研究

## 核心原则

- 最新市场状态优先于旧新闻叙事。
- 历史信息保留，但只能作为背景、类比、因果链，不得替代当前状态。
- 时间敏感任务里，如果关键最新数据缺失，就必须降低精度，不得硬给高精度执行建议。

## 时间线合同

每个候选逻辑至少要落成 4 段时间线：

1. `历史背景`
2. `最近 1-7 天的新催化`
3. `最新市场状态`
4. `当前结论 now`

输出时必须明确：

- `Market data as of:`
- `News data as of:`
- `Timeline span:`
- `Completeness status: COMPLETE | PARTIAL | MISSING`
- `Precision level: EXECUTABLE | DIRECTIONAL_ONLY | WATCHLIST | NOT_EXECUTABLE`
- `Critical missing fields:`
- `Fallback sources used:`
- `Mixed freshness risk: LOW | MEDIUM | HIGH`
- `Timeline integrity: COHERENT | PARTIAL | BROKEN`

如果涉及期权，还必须补：

- `Options data as of:`
- `Options data status: COMPLETE | PARTIAL | MISSING`
- `Open interest status: COMPLETE | PARTIAL | MISSING`
- `Bid-ask status: COMPLETE | PARTIAL | MISSING`
- `Expiry-window fit: MATCHED | PARTIAL | UNKNOWN`

## 精度降级规则

### 允许 `EXECUTABLE`

仅当以下条件成立时：

- 最新价格 / 技术面 / 新闻窗口齐全
- 关键数据 freshness 可交代
- 期权任务有真实期权链、IV、OI、流动性或等价数据
- quant 输入不是模板
- 关键分析 agent 已形成 task-local 输出

### 只能 `DIRECTIONAL_ONLY`

出现任一情况：

- 有方向判断，但缺少最新技术确认
- 期权链缺失，只能判断 underlying 方向
- mixed freshness 明显，但不足以彻底否定 thesis

### 只能 `WATCHLIST`

出现任一情况：

- 当前缺触发确认
- 关键数据接近过期
- 方向未被证伪，但也未获当前状态确认

### 必须 `NOT_EXECUTABLE`

出现任一情况：

- 缺最新价格 / 技术面 / 资金面中的关键项
- 期权任务没有期权链却还想给 strike/expiry
- quant 输入仍是模板
- 关键 agent 结果缺失或失败

## Reversal Vs Continuation Veto

- 如果报告要给 `short/put`，但当前状态已经明显 `oversold / 超卖 / RSI≈30 或以下`，默认不能直接给 `EXECUTABLE`。
- 只有在以下任一条件存在时，才允许继续 bearish thesis：
  - fresh continuation confirmation
  - failed bounce confirmation
  - breakdown after rebound
- 否则只能输出：
  - `WAIT`
  - `WATCHLIST`
  - 或 `反弹后再空`

- 对称地，如果报告要给 `long/call`，但当前状态已经明显 `overbought / 超买 / RSI≈70 或以上`，默认也不能直接给 `EXECUTABLE`，除非有 fresh breakout confirmation 或 pullback plan。

## Task-local 落盘要求

当任务是金融时效任务时，优先维护这些文件：

- `sources/fetch-log.jsonl`
- `sources/live-market-snapshot.json`
- `sources/data-completeness.json`
- `sources/news-event-log.jsonl`

如果后端是 `FinanceMCP/Tushare` 这类有限流接口，先通过：

```bash
python3 ./scripts/finance-data-budget-guard.py ensure-ledger --task-slug <task-slug>
python3 ./scripts/finance-data-budget-guard.py reserve --task-slug <task-slug> --endpoint stock_data --symbol <symbol> --budget-key tushare-stock-data --per-minute 2 --per-day 5 --cooldown-seconds 65
```

若返回 `FINANCE_BUDGET_WAIT`，先等待再重试，不要让多个 lane 同时撞同一个分钟配额。

对新闻 / 财报 / 政策 / 地缘政治 / 板块催化，还要落盘：

```bash
python3 ./scripts/finance-news-event-ledger.py ensure-ledger --task-slug <task-slug>
python3 ./scripts/finance-news-event-ledger.py append-event --task-slug <task-slug> --headline '<HEADLINE>' --source '<SOURCE>' --symbol '<SYMBOL>' --published-at '<ISO>' --event-type '<EVENT_TYPE>' --driver-type '<DRIVER_TYPE>' --direction-bias '<BULLISH|BEARISH|VOLATILE|MIXED>' --impact-horizon '<HORIZON>' --confidence '<LOW|MEDIUM|HIGH>' --url '<URL>'
```

每次 live fetch / fallback 之后，用：

```bash
python3 ./scripts/finance-data-budget-guard.py finalize --task-slug <task-slug> --request-id <id> --status success|fallback|error
python3 ./scripts/finance-data-budget-guard.py set-completeness --task-slug <task-slug> --symbol <symbol> --field <field> --status complete|partial|missing --as-of <iso> --source <source>
python3 ./scripts/finance-data-budget-guard.py upsert-snapshot --task-slug <task-slug> --symbol <symbol> --as-of <iso> --source <source> --payload-json '<json>'
```

最后可统一生成 freshness / timeline summary：

```bash
python3 ./scripts/finance-timeline-fusion.py --task-slug <task-slug> --format markdown --output ./tasks/<task-dir>/reports/finance-timeline-summary.md
```

最终金融报告应固定包含一个 `## 事件驱动因子` section，并优先从 `news-event-log.jsonl` 提取，不要只在 prose 里顺手提一下。

即使暂时还没有自动化生成，也要让 worker 在 worklog 里明确记录：

- 哪些最新数据拿到了
- 哪些没拿到
- 何时拿的
- 用了什么回退源

## 期权红线

- 没有真实期权链，不得给 precise strike / precise expiry / IV judgement。
- 此时只能输出：
  - `underlying direction`
  - `structure candidate`
  - `missing fields`

不要把这类输出伪装成可直接下单的期权剧本。
