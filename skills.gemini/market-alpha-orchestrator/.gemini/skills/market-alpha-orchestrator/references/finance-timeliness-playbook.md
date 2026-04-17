# Finance Timeliness Playbook

这个文件定义 market-alpha 在高时效金融任务中的硬规则。

## 适用范围

- `style=short`
- `depth=trade-plan|derivatives`
- 涉及财报、新闻、行情、技术面、资金面、期权
- 任何 `h24-48` / `d3-7` / `w1-2` 的交易 intelligence 任务

## 当前信息优先级

按这个顺序判断，不要倒过来：

1. 当前价格 / 最新市场状态
2. 最近 1-3 个交易日的技术确认
3. 新催化与新新闻
4. 历史背景 / 历史类比

历史背景可以解释，但不能压过当前市场状态。

## Tushare / FinanceMCP 节流规则

对 `Tushare` 背后的 `stock_data` 等接口，不要让多个 lane 同时自由开火。

先建立 task-local ledger：

```bash
python3 ./scripts/finance-data-budget-guard.py ensure-ledger --task-slug <task-slug>
```

每次 live 请求前先 reserve：

```bash
python3 ./scripts/finance-data-budget-guard.py reserve \
  --task-slug <task-slug> \
  --endpoint stock_data \
  --symbol <symbol> \
  --budget-key tushare-stock-data \
  --per-minute 2 \
  --per-day 5 \
  --cooldown-seconds 65
```

若返回 `FINANCE_BUDGET_WAIT`：

- 等待后重试
- 或切换到明确标记 freshness 的 fallback
- 不要让所有 lane 一起退化成旧网页数据

请求完成后，回写：

- `sources/fetch-log.jsonl`
- `sources/live-market-snapshot.json`
- `sources/data-completeness.json`
- `sources/news-event-log.jsonl`

对新闻 / 财报 / 政策 / 地缘政治 / 板块催化，再追加：

```bash
python3 ./scripts/finance-news-event-ledger.py ensure-ledger --task-slug <task-slug>
python3 ./scripts/finance-news-event-ledger.py append-event --task-slug <task-slug> --headline '<HEADLINE>' --source '<SOURCE>' --symbol '<SYMBOL>' --published-at '<ISO>' --event-type '<EVENT_TYPE>' --driver-type '<DRIVER_TYPE>' --direction-bias '<BULLISH|BEARISH|VOLATILE|MIXED>' --impact-horizon '<HORIZON>' --confidence '<LOW|MEDIUM|HIGH>' --url '<URL>'
```

在 synthesis / report 阶段，用：

```bash
python3 ./scripts/finance-timeline-fusion.py --task-slug <task-slug> --format markdown --output ./tasks/<task-dir>/reports/finance-timeline-summary.md
```

把 ledger 压缩成 `Data Freshness & Completeness`，不要手工猜 freshness。

同时生成事件驱动摘要：

```bash
python3 ./scripts/finance-news-event-ledger.py summary --task-slug <task-slug>
```

最终报告必须有 `## 事件驱动因子` section，明确写出：

- 哪些 headline 真正进入了决策链
- 对哪个 symbol 生效
- 是 bullish / bearish / volatile / mixed
- 作用的 horizon 是什么

## Data Freshness & Completeness

最终报告必须固定包含一个 section：

```markdown
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
```

取值要求：

- `Completeness status`: `COMPLETE | PARTIAL | MISSING`
- `Precision level`: `EXECUTABLE | DIRECTIONAL_ONLY | WATCHLIST | NOT_EXECUTABLE`
- `Options data status`: `COMPLETE | PARTIAL | MISSING`
- `Mixed freshness risk`: `LOW | MEDIUM | HIGH`
- `Timeline integrity`: `COHERENT | PARTIAL | BROKEN`
- `Open interest status`: `COMPLETE | PARTIAL | MISSING`
- `Bid-ask status`: `COMPLETE | PARTIAL | MISSING`
- `Expiry-window fit`: `MATCHED | PARTIAL | UNKNOWN`

## 精度降级规则

### 允许 `EXECUTABLE`

仅当：

- 关键最新价格和技术面齐全
- 关键新闻 / 事件时间点明确
- 如果是期权任务，真实期权链齐全
- quant 输入不是模板
- 关键 agent 全部完成并落盘

### 只能 `DIRECTIONAL_ONLY`

当：

- 能判断 underlying 方向
- 但还不能给 precise strike / expiry / probability / precise risk score

### 只能 `WATCHLIST`

当：

- 逻辑还在，但当前触发不完整
- 关键确认条件尚未出现

### 必须 `NOT_EXECUTABLE`

当：

- 数据 freshness 明显混杂
- 关键技术数据缺失
- 期权链缺失却还想给具体合约
- quant 还是模板
- 关键 agent 缺席

## Reversal Vs Continuation Veto

- 若策略方向是 `short / put`，但当前技术状态已经显著 `oversold / 超卖 / RSI≈30 或以下`，默认禁止直接给 `EXECUTABLE`。
- 只有在 fresh continuation confirmation 存在时才允许继续：
  - 反弹失败
  - 破位延续
  - 新鲜负面催化继续强化
- 否则必须降级为：
  - `WAIT`
  - `WATCHLIST`
  - `反弹后再空`

- 若策略方向是 `long / call`，但当前技术状态已经显著 `overbought / 超买 / RSI≈70 或以上`，同理禁止直接给 `EXECUTABLE`，除非有 breakout continuation 或 pullback plan。

## 期权红线

下面这些任一缺失，就不要给 precise option plan：

- 实时期权链
- IV / skew
- OI
- bid/ask / liquidity
- 到期日与催化窗口的匹配确认

此时最多输出：

- underlying direction
- structure candidate
- missing_fields

## Synthesis 红线

- 承认数据缺失之后，不能在下一段继续给高精度期权参数。
- 如果 report 自己写了“无法推荐具体行权价 / 到期日”，那最终结论也必须同步降级。
- 如果 technical/quant/freshness 只覆盖部分标的，不要把未覆盖标的包装成“最优”。
