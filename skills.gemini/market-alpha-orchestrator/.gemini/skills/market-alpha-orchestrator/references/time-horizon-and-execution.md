# Time Horizon And Execution

这个文件定义“时间周期”不只是研究窗口，也是**用户可执行性约束**。

## 核心概念

### 1. signal_market

最先释放交易信息优势的市场。

例子：

- 美股 AI 龙头
- LME 铜
- COMEX 黄金
- 海外政策 / 利率市场

### 2. execution_market

用户更适合真正执行交易的市场。

例子：

- A 股
- 港股
- 白天更易交易的期货合约

### 3. execution_profile

- `east-asia-cash-hours`
  - 默认假设
  - 更适合 A 股、港股、亚洲日间时段
- `us-overnight-ok`
  - 用户明确接受夜盘或美股时段盯盘
- `global-flex`
  - 用户可跨时区灵活执行

## 周期先决定研究方向

具体周期分层见 `references/horizon-taxonomy.md`。

同一个标的在不同周期下，研究重点会完全不同：

- `h24-48`
  - 看信号传导、催化密度、执行窗口
- `d3-7`
  - 看资金持续性、事件扩散、板块共振
- `m1-3`
  - 看业绩与行业趋势
- `y1-3`
  - 看竞争格局、资本开支、长期供需

## 短线规则

### 24-48h

这是最难的窗口，因为：

- 信息半衰期极短
- 拥挤度极高
- 对执行节奏要求极严

所以报告要先判断：

1. 这个机会是不是已经太公开
2. 它还能不能在下一个交易时段继续扩散
3. 用户能不能在自己的作息下真正执行
4. 当前选用的是哪个 `horizon`
5. 进入与退出窗口是否与用户可执行时间一致

### East Asia 用户的默认约束

如果用户人在东亚，且没有明确说能做美股夜盘：

- 美股常常更适合作为 `signal_market`
- A 股 / 港股更适合作为 `execution_market`

这意味着：

- 可以写：
  - `NVDA -> 兆易创新 / A股算力映射`
- 不应该默认写：
  - `直接买 NVDA，今晚再卖`

除非用户明确接受这种作息与执行方式。

## 报告中必须增加的字段

| 标的 | signal_market | execution_market | session_fit | monitor_load |
|------|---------------|------------------|-------------|--------------|

其中：

- `session_fit`
  - `native-hours`
  - `overnight-manageable`
  - `not-recommended`
- `monitor_load`
  - `low`
  - `medium`
  - `high`

再额外加：

- `horizon`
- `entry_window`
- `exit_window`
- `max_holding_period`

## Long 规则

Long 不追求“今天晚上必须卖掉”，但要求更高的逻辑可靠性。

更合理的目标不是“100% 正确”，而是：

- 跨周期逻辑稳定
- 证据链厚
- 关键假设少且清楚
- 就算短期波动，也不轻易伤害长期 thesis

所以 long 报告要更像：

- 可靠性分层
- 证据密度评估
- thesis 失效条件

而不是短线那种高频触发器列表。
