# Multi-Factor Methodology

这个文件定义 long / short 都能复用的一套多因子骨架。

## 核心原则

- 先分市场，再分风格，再评分
- 先结构化数据，再新闻叙事
- 评分只是排序工具，不是替代判断

## 推荐因子层

### 1. Macro / Liquidity

- 利率
- 信用
- 汇率
- 流动性
- 政策方向

### 2. Fundamental / Quality

- 收入与利润趋势
- 现金流质量
- ROE / ROA / 净利率
- 负债与资本结构
- 业务集中度与护城河

### 3. Valuation

- PE / PB / EV 类分位
- 同业对比
- 隐含兑现要求

### 4. Sentiment / Flow

- 主力资金流
- 基金行为
- 龙虎榜
- 融资融券
- 新闻热度变化

### 5. Technical / Market Structure

- 趋势
- 波动率
- 分钟线确认
- ATR / 均线 / MACD / KDJ / BOLL

### 6. Catalyst

- 业绩
- 政策
- 产品 / 订单
- 事件驱动
- 供需变化

## 评分模板

### Long

建议权重：

- Macro / Liquidity: 20
- Fundamental / Quality: 25
- Valuation: 20
- Sentiment / Flow: 15
- Technical: 10
- Catalyst: 10

### Short

建议权重：

- Catalyst: 25
- Technical / Market Structure: 25
- Sentiment / Flow: 25
- Liquidity / Volatility: 15
- Fundamental sanity check: 10

## 报告内的最小表格

| 标的 | 市场 | 风格 | 主要因子 | 触发器 | 风险 | 失效条件 |
|------|------|------|----------|--------|------|----------|

## 风险管理

无论 long 还是 short，都至少给：

- 波动率或 ATR 参考
- 止损条件
- 时间止损
- 仓位建议
- 哪种新信息会让逻辑失效

