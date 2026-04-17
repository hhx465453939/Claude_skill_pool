# Short Alpha Hunt

这个文件定义真正用于短线 Alpha 狙击的工作流。

## 目标

不是去解释“今天为什么会跌/会冲高回落”。

而是尽量在 **共识形成前**，找到仍有爆发力的 **买入机会**。

## 默认时间框架

- 默认：`2-15` 个交易日
- 如果用户明确要求：
  - `24h`
  - `1-2天`
  - `日内`
  才切到更短周期

没有明确要求时，不要把短线默认收缩成“明天就兑现”的事件后交易。

## 24-48h 的额外难点

`24-48h` 不是普通短线，它是最难的一档：

- 信息必须更快
- 执行必须更顺手
- 错误赔率更高

因此：

- 允许胜率低于 long
- 但必须更重视执行可达性和赔率
- 不能把“美股公开事件后需要今晚盯盘卖出”的名字，默认当成东亚用户的第一执行方案

## 先过滤，再找机会

### 第一层：拥挤度毒丸过滤

先问下面这些问题：

- 这个事件是否已经被所有主流媒体、头部卖方、社交热榜反复覆盖？
- 价格是否已经在催化前连续大涨？
- RSI / 换手 / 讨论热度是否过热？
- 它更像“大家都知道会发生什么”，还是“市场还没意识到哪一部分最关键”？

如果答案偏向前者：

- 不要输出方向性多头买点
- 降级为：
  - `crowded-event`
  - `volatility-only`
  - 或直接剔除

## 真的 Alpha 从哪来

### 1. 隐性催化剂预期差

重点找：

- 供应链核心节点替换
- 小范围订单 / 招标 / 出货节奏变化
- 边角政策与非主叙事受益
- 业务结构或产品节奏的隐形加速
- 被主流叙事遮蔽的二阶受益标的

### 2. 静默期筹码与脉冲

重点找：

- 缩量沉淀后的放量脉冲
- 量价关系优于板块平均
- 异常换手但并未大热
- 单笔成交质量改善

### 3. 反直觉强势

重点找：

- 大盘明显走弱时的相对抗跌
- 风险事件日里仍有净流入
- 同板块里最早止跌、最先恢复趋势的名字

### 4. 资金行为共振

必须交叉这些代理：

- `money_flow`
- `margin_trade`
- `block_trade`
- `dragon_tiger_inst`

不是单独某个指标好看就够了，至少要出现两组以上一致信号。

### 5. 历史类比与证伪

每个候选都要问：

- 它更像历史上的启动前夜，还是拉升末端？
- 这次如果错了，最可能错在哪里？
- 哪条证据一旦被推翻，整个买点就失效？

### 6. signal_market vs execution_market

每个候选都必须明确：

- `signal_market`
- `execution_market`
- `session_fit`

如果：

- `signal_market=US`
- 用户默认在东亚现金时段执行

则更优先寻找：

- A 股跟随
- 港股跟随
- 或亚洲时段更易执行的相关合约

## 推荐 agent 分工

短线 Alpha Hunt 应优先使用专用 agent 组：

- `planner`
  - 把任务切成催化、微观结构、拥挤度、历史类比、量化验证几条线
- `truth-collector`
  - 先把现货真值、时间戳、主/次来源和 cross-check diff 落到 truth ledger
- `universe-builder`
  - 强制从主题下钻到单名股池，不允许停在 ETF 层
- `catalyst-hunter`
  - 找 2-15 个交易日前的隐性催化
- `microstructure-hunter`
  - 盯量价、脉冲、相对强势、分钟线
- `crowding-killer`
  - 负责把公开共识交易和潜在接盘局剔掉
- `history-analog`
  - 找相似启动前夜和失败样本
- `single-name-driller`
  - 验证个股层预期差、订单/产品节奏、estimate revision、relative strength、flow quality
- `strategy-miner`
  - 把重复出现的 setup 注册进 task-local strategy lab，而不是只留在 prose
- `quant-verifier`
  - 算相对强弱、波动率、异常换手、资金行为评分
  - 必须运行 task 内真实脚本，不得只口头输出
- `synthesis-analyst`
  - 只整合能穿过证伪与拥挤过滤的标的
- `reviewer`
  - 检查是否又滑回“解释卖点”而不是“狙击买点”
- `report-generator`
  - 生成正式报告并交付

## 报告合同

短线狙击报告至少要多出这几列：

| 标的 | alpha_class | hidden_catalyst | crowding_status | signal_market | execution_market | session_fit | trigger | invalidation | horizon |
|------|-------------|-----------------|-----------------|---------------|------------------|-------------|---------|--------------|---------|

其中：

- `alpha_class`
  - `pre-consensus-buy`
  - `mispriced-catalyst`
  - `relative-strength-breakout`
  - `crowded-event`
  - `volatility-only`

只要不是前 3 类，就不应该当核心多头买点。

## 量化最小交付

如果报告里出现：

- 置信度
- 技术评分
- 胜率
- 盈亏比
- 回测

则至少要有一份 task 内量化输出，例如：

- `reports/quant/factor-score.json`
- `reports/quant/backtest-summary.json`

并在报告中引用这些文件路径。

## 风格红线

- 不要把“众人皆知的重磅大会”当默认首选方向
- 不要把“可能冲高回落”的东西排第一
- 不要为了热闹牺牲赔率
- 真正的短线 Alpha 必须更像狩猎，而不是新闻复述
- 对 `3个月` 左右的美股 hunt，默认不得 ETF-only；若没有单名股通过，必须由 reviewer 显式写出 `NO_SINGLE_NAME_PASSED` 与 ETF 降级理由
