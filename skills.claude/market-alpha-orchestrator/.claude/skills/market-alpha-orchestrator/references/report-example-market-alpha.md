# Market Alpha Report Example

下面是一份 report-generator 应该模仿的结构示例。

````markdown
# 美股 24-48h Lead-Follow 短线交易报告

**报告编号**: MA-2026-03-16-EXAMPLE
**生成时间**: 2026-03-16 14:00 CST
**市场**: `signal_market=US` / `execution_market=CN`
**风格**: `short`
**模式**: `lead-follow`
**时间框架**: `h24-48`

---

## 执行摘要

- 核心结论：
  - 今晚美股只作为信号市场
  - 明日更优执行落点在 A 股映射链
- 首选执行方向：
  - A 股算力映射
  - 港股相关 AI 硬件映射

## 市场与周期判断

- signal_market: US
- execution_market: CN
- session_fit: native-hours
- lead_lag_window: 8-18 小时
- entry_window: 下一个 A 股现金时段开盘后 15-60 分钟
- exit_window: 次日收盘前或触发失效条件
- max_holding_period: 2 个交易日

## Data Freshness & Completeness

- Market data as of: `2026-03-16 13:55 CST`
- News data as of: `2026-03-16 13:45 CST`
- Options data as of: `not required for this underlying-only lead-follow setup`
- Options data status: `MISSING`
- Timeline span: `2026-03-12 earnings repricing -> 2026-03-16 US close signal -> next CN cash session execution`
- Completeness status: `COMPLETE`
- Precision level: `EXECUTABLE`
- Critical missing fields: `none`
- Fallback sources used: `none`

## Truth And Review

- Truth ledger:
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/derivatives/underlying-truth-ledger.json`
- Reviewer verdict:
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/review/reviewer-verdict.json`
- Single-name mandate:
  - `HAS_SINGLE_NAME`

## 事件驱动因子

### 1. NVDA / SOX overnight signal
- Symbol: `NVDA`
- Source: `market-wide news + post-close tape`
- Published at: `2026-03-16 05:30 UTC`
- Driver type: `AI hardware demand`
- Direction bias: `BULLISH`
- Impact horizon: `h24-48`

### 2. CN execution window
- Symbol: `603986.SH`
- Source: `cross-market lead-follow mapping`
- Published at: `2026-03-16 09:15 UTC`
- Driver type: `execution-market follow-through`
- Direction bias: `BULLISH`
- Impact horizon: `h24-48`

## 候选池

| 标的 | alpha_class | signal_market | execution_market | crowding_status | 核心逻辑 |
|------|-------------|---------------|------------------|-----------------|----------|
| 兆易创新 | pre-consensus-buy | US | CN | low | 美股 AI 芯片链信号向 A 股扩散，A 股映射拥挤度更低 |
| XXX | mispriced-catalyst | US | HK | medium | 海外先行，港股次日响应 |

## 交易计划

### 兆易创新

- 策略标签：`lead-follow`
- 方向：做多
- 订单类型：`limit-ladder`
- 入场触发：NVDA / SOX 收盘强于纳指，且 A 股开盘前同主题港股未出现一致性抢筹
- 建议入场区间：`126.40-128.20`
- 加仓条件：首小时放量突破前高，且 5 分钟 VWAP 持续上移
- 减仓条件：T1 达成后先减 1/3；若量能衰减再减 1/3
- 止盈目标位：`T1=132.50`, `T2=136.80`
- 动态止损：T1 达成后抬升止损到开仓成本上方 0.5%
- 时间止损：若 T+1 14:30 前未出现趋势延续，则主动平仓
- 核心止损位：`123.80`
- 失效条件：
  - A 股开盘后映射不成立
  - 量价不确认
  - 美股主信号被快速证伪
- 建议仓位：首仓 4%，加仓后总仓不超过 7%
- 滑点预算：`25 bps`
- 退出窗口：次日收盘前或触发失效条件
- 最大持有时长：2 个交易日
- 预估风险收益比：`1:2.6`

## 风险矩阵

| 风险 | 级别 | 说明 |
|------|------|------|
| 拥挤度抬升 | 中 | 若 A 股映射开盘即一致性抢筹，赔率下降 |
| 主信号证伪 | 高 | 若美股原始信号被市场否定，映射逻辑失效 |

## 数据缺口

- 当前未接入完整期权链
- 当前未接入盘口级订单簿回测

## Bot Handoff

```json
{
  "status": "EXECUTABLE",
  "task_path": "./tasks/2026-03-16-us-stock-short-signal-hunt",
  "plans": [
    {
      "ticker": "603986.SH",
      "name": "兆易创新",
      "signal_market": "US",
      "execution_market": "CN",
      "direction": "long",
      "setup_type": "lead-follow",
      "entry_trigger": "NVDA / SOX 收盘强于纳指，且 A 股开盘前未出现映射链一致性抢筹",
      "entry_zone": {
        "min": 126.4,
        "max": 128.2,
        "unit": "CNY"
      },
      "order_type": "limit-ladder",
      "position_size_pct": 4,
      "add_on_trigger": "首小时放量突破前高且 5m VWAP 上移",
      "reduce_on_trigger": "T1 达成后减 1/3，量能衰减再减 1/3",
      "stop_loss": {
        "price": 123.8,
        "type": "hard"
      },
      "take_profit": [
        {"label": "T1", "price": 132.5},
        {"label": "T2", "price": 136.8}
      ],
      "trailing_stop": "T1 达成后抬升止损到开仓成本上方 0.5%",
      "time_stop": "T+1 14:30",
      "max_holding_period": "2 trading days",
      "slippage_budget_bps": 25,
      "invalidation": "A 股开盘后映射不成立，或美股主信号被快速证伪"
    }
  ]
}
```

## Quant Evidence

- Script path:
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/scripts/market-alpha-quant-compass.py`
- Input path:
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/scratch/quant/candidate-factors.csv`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/scratch/quant/signal-backtest.csv`
- Output path:
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/factor-score.json`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/factor-score.csv`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/factor-score.png`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/backtest-summary.json`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/backtest-summary.csv`
  - `./tasks/2026-03-16-us-stock-short-signal-hunt/reports/quant/backtest-summary.png`
- Method used:
  - `score`
  - `backtest-forward`
- Summary:
  - 最高 alpha_score 候选：兆易创新 / XXX / YYY
  - `horizon=1` 命中率 0.50，平均收益 0.01
  - `horizon=2` 命中率 1.00，平均收益 0.03

### Quant Charts

![Factor Score Chart](./quant/factor-score.png)

![Backtest Summary Chart](./quant/backtest-summary.png)
````

## 要点

- `Quant Evidence` 是固定 section，不是可有可无
- `Bot Handoff` 也是固定 section，用于 Rust / 自动化执行
- `Truth And Review` 用来对齐 truth ledger 和 reviewer verdict，不要把这两份机器文件只留在 task 里不在报告里提及
- 图片引用用 markdown 原生语法
- 如果没有量化结果文件，就不要生成这个 section
- 如果有量化结果文件，就必须把 JSON / CSV / PNG 全部引用清楚
- 如果不能形成可执行策略，不要伪装成交易建议；改为 `NOT_EXECUTABLE`
