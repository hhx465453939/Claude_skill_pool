# FinanceMCP Capability Map

本地 MCP 注册名：`finance-mcp-local`

实际入口来自：

- `workspace/config/mcporter.json`
- `/mnt/500G-1/Development/FinanceMCP/build/index.js`

注意：

- 配置里出现入口路径，不等于容器运行时一定可见
- 当前 `repo/docker-compose.yml` 已挂载 `/mnt/500G-1/Development`
- 所以像 `/mnt/500G-1/Development/FinanceMCP/build/index.js` 这样的入口，在 compose reload 后应当容器内可见
- 若仍失败，优先排查 server 启动与调用方式，而不是继续怀疑 volume
- 不能只看 `mcporter.json` 就宣称 FinanceMCP 可用，也不能只看路径外观就下结论；必须做容器内可见性验证

## 当前可见工具

### 时间与新闻

- `current_timestamp`
- `finance_news`
- `hot_news_7x24`

### 行情与指数

- `stock_data`
  - 支持：`cn` `us` `hk` `fx` `futures` `fund` `repo` `convertible_bond` `options` `crypto`
  - 支持技术指标：`macd` `rsi` `kdj` `boll` `ma`
- `stock_data_minutes`
  - 支持：A 股、加密
  - 周期：`1MIN` `5MIN` `15MIN` `30MIN` `60MIN`
- `index_data`
- `csi_index_constituents`

### 宏观

- `macro_econ`
  - `shibor`
  - `lpr`
  - `gdp`
  - `cpi`
  - `ppi`
  - `cn_m`
  - `cn_pmi`
  - `cn_sf`
  - `shibor_quote`
  - `libor`
  - `hibor`

### 公司与财务

- `company_performance`：A 股
- `company_performance_hk`：港股
- `company_performance_us`：美股

### 基金与经理

- `fund_data`
- `fund_manager_by_name`

### 资金行为 / 微观结构

- `money_flow`
- `margin_trade`
- `block_trade`
- `dragon_tiger_inst`

### 其他工具

- `convertible_bond`

## 按场景推荐工具组合

### A 股 long

- `macro_econ`
- `index_data`
- `csi_index_constituents`
- `company_performance`
- `money_flow`
- `fund_data`
- `finance_news`

### A 股 short

- `stock_data_minutes`
- `stock_data`
- `money_flow`
- `margin_trade`
- `block_trade`
- `dragon_tiger_inst`
- `hot_news_7x24`

### 美股 long

- `stock_data`
- `company_performance_us`
- `finance_news`
- `hot_news_7x24`
- 原生 web/fetch 补美联储、行业、卖方观点

### 港股 long

- `stock_data`
- `company_performance_hk`
- `finance_news`

### 商品 / 期货

- `stock_data` with `market_type=futures`
- `macro_econ`
- `finance_news`

### 可转债 / 基金

- `convertible_bond`
- `fund_data`
- `fund_manager_by_name`
- `stock_data`

### 期权 / 衍生品结构

- `stock_data` with `market_type=options`
- `index_data`
- `stock_data` for underlying
- `finance_news`

## 已知边界

当前 FinanceMCP 没看到专门的：

- 期权链
- Greeks
- 隐含波动率曲面
- Open Interest
- 美股期权专用链路
- Level-2 原始盘口

所以：

- 可以做方向判断、结构选择、标的筛选
- 不能假装已经完成完整期权链优化

## 自检

如果怀疑工具能力已经变化，运行：

```bash
node workspace/skills/market-alpha-orchestrator/scripts/inspect-finance-mcp.js --format md
```
