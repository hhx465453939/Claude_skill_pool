---
name: market-alpha-orchestrator
description: 多市场 long/short 交易研究编排技能。用于 A股、美股、港股、期货、期权、基金、可转债、加密等场景的选股、标的深研、交易计划和衍生品结构设计，优先调用 FinanceMCP，并按需串联 superpowers、deep-research、feishu-file-transfer 与稳定报告交付脚本。
version: 0.1.0
---

# Market Alpha Orchestrator

把 `FinanceMCP`、`deep-research`、`superpowers`、`deliver-report.sh` 和飞书文件发送能力编排成一个统一的市场研究与交易输出工作流。

并且要求：涉及量化验证时，必须在 task 内留下真实可执行的脚本和结果文件，而不是只口头声称“Quant Verifier 已完成验证”。

## 何时使用

当用户要你做以下任何一类事时使用本 skill：

- 跨市场选股或选合约：A 股、美股、港股、期货、基金、可转债、加密
- 从宏观到行业到个股的 long 框架研究
- 基于分钟线、资金流、盘口代理信号的 short 框架筛选
- 对高价值标的做深研、风险评估、交易计划
- 先筛后研，再落到执行建议或衍生品结构
- 要求稳定报告、统一命名、落盘到 `workspace/report/` 并可发飞书

不要在以下场景触发：

- 只查一个价格、一个代码、一个时间点
- 只问概念解释，不需要研究编排

## 先做什么

1. 先把请求标准化到 4 个维度：
   - `market`: `cn` / `us` / `hk` / `futures` / `options` / `fund` / `convertible_bond` / `crypto` / `multi`
   - `style`: `long` / `short` / `hybrid`
   - `depth`: `scan` / `deep-dive` / `trade-plan` / `derivatives`
   - `horizon`: `auto` / `h24-48` / `d3-7` / `w1-2` / `w2-4` / `m1-3` / `m3-6` / `m6-12` / `y1-3` / `y3-5` / `y10-plus`
   - `engine`: `auto` / `hybrid` / `superpowers` / `deep-research`
   - `alpha_mode`: `normal` / `hunt` / `lead-follow` / `crowded-event` / `volatility-only`
   - `execution_profile`: `east-asia-cash-hours` / `us-overnight-ok` / `global-flex`
2. 复杂任务先建 task session：

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-bootstrap.sh \
  --task-slug "<slug>" \
  --engine "<auto|hybrid|superpowers|deep-research>" \
  --market "<market>" \
  --style "<long|short|hybrid>" \
  --alpha-mode "<normal|hunt|lead-follow|crowded-event|volatility-only>" \
  --horizon "<auto|h24-48|d3-7|w1-2|w2-4|m1-3|m3-6|m6-12|y1-3|y3-5|y10-plus>" \
  --instrument "<equity|sector|index|commodity|derivative|fund>" \
  --objective "<goal>"
```

3. 总是先读 `references/finance-mcp-capability-map.md`
4. 再按模式只读需要的参考件：
   - 涉及 OpenClaw 原生并发 / subagents / task-local prompt pack -> `references/native-subagents-runtime.md`
   - 周期推断 / 默认周期 / 进入退出窗口 -> `references/horizon-taxonomy.md`
   - `long` -> `references/long-framework.md`
   - `short` -> `references/short-framework.md`
   - `short + alpha hunt` -> `references/short-alpha-hunt.md`
   - `short + lead-follow` -> `references/short-lead-follow.md`
   - 涉及 24-48h / 东亚执行 / 美股先行-A股跟随 -> `references/time-horizon-and-execution.md`
   - 涉及量化评分 / 回测 / 简单模型 -> `references/quant-compass.md`
   - 涉及时效性金融数据合同 / 精度降级 / options precision guard -> `references/finance-timeliness-playbook.md`
   - 两者都要评分/交易计划 -> `references/multi-factor-methodology.md`
   - 涉及交付 -> `references/reporting-and-delivery.md`
   - 需要固定报告结构 -> `references/report-example-market-alpha.md`

如果不确定本地 FinanceMCP 当前到底暴露了哪些工具，运行：

```bash
node workspace/skills/market-alpha-orchestrator/scripts/inspect-finance-mcp.js --format md
```

不要靠猜测判断 MCP 是否可用。

- `inspect-finance-mcp.js` 只能说明配置存在和工具快照可见，不代表容器内入口文件一定可执行
- 当前 `repo/docker-compose.yml` 已挂载 `/mnt/500G-1/Development`
- 所以 `finance-mcp-local` / `tavily-mcp-local` 这类指向 `/mnt/500G-1/Development/...` 的入口，在 compose reload 后应当容器内可见
- 对这些 MCP，先做容器内文件可见性验证；若文件存在，再继续排查 server 启动或路由问题；只有这样仍失败才降级到 web-only
- 不要臆造 `localhost:3000/mcp/...` 这类未证实的本地 HTTP 路由

如果任务涉及量化验证、评分、简单回测、线性模型或胜率/盈亏比估算，必须初始化 task 内量化脚手架：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-quant-setup.py \
  --task-slug "<slug>" \
  --style "<style>" \
  --horizon "<horizon>" \
  --objective "<goal>"
```

现在 `market-alpha-bootstrap.sh` 还会自动补一层动态数据层快照，生成：

- `workspace/config/cache/market-alpha-tool-registry.json`
- `tasks/.../reports/data-layer/tool-registry.json`
- `tasks/.../reports/data-layer/router-preview.json`
- `tasks/.../reports/data-layer/access-log.jsonl`
- `tasks/.../reports/data-layer/health-report.json`
- `tasks/.../reports/data-layer/routing-dashboard.json`
- `tasks/.../capsules/task-capsule.md|json` 中的 data-layer 摘要
- `tasks/.../capsules/skill-brief.md` 中的路由规则
- 新生成的 `agents/*.md` 会按 agent 角色自动注入 primary/fallback route，避免所有 lane 都从同一套泛化 MCP 猜测起步

如果 task 还没有 capsule（典型是 hybrid 路径），这一步会补建最小 capsule/brief，确保后续 agent 能直接读取路由上下文。

如果需要单独刷新：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py discover

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py bootstrap-task \
  --task-slug "<slug>" \
  --market "<market>" \
  --style "<style>" \
  --instrument "<instrument>" \
  --horizon "<horizon>" \
  --alpha-mode "<alpha-mode>" \
  --objective "<goal>"

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py healthcheck --probe-finance

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py dashboard

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-data-layer.py execute-task \
  --task-json '{"type":"utility","category":"current_timestamp"}' \
  --args-json '{}'
```

如果 task 已经生成 `agents/*.md`，还要准备 OpenClaw 原生 subagent prompt pack：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-subagents.py \
  --task-slug "<slug>"
```

这会生成：

- `tasks/.../native-subagents/manifest.json`
- `tasks/.../native-subagents/coordinator-playbook.md`
- `tasks/.../native-subagents/prompts/*.md`
- `tasks/.../agents.jsonl` 的 durable orchestration state 将由 coordinator bridge 持续回写

然后立刻做两件事：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-coordinator.py \
  validate \
  --task-slug "<slug>"

python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-coordinator.py \
  status \
  --task-slug "<slug>"
```

主 agent 后续必须使用 `manifest.json` 里的 `spawn_payload` 调 `sessions_spawn`，并在每次 accepted 后马上用 coordinator bridge 记录 `runId` / `childSessionKey`，而不是只说“Wave 1 已启动”。

如果用户要求把整个 task 打包发回聊天，运行：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-package-task.py \
  --task-slug "<slug>" \
  --include-scratch
```

## 工作流

### 1. 标准化请求

把用户请求转成下面这种内部摘要，再继续动作：

```text
目标市场:
目标对象:
研究风格:
输出深度:
时间框架:
是否需要直接交易计划:
是否需要衍生品结构:
```

### 2. 选择执行引擎

- `auto`
  - `style=short` 默认转 `deep-research`
  - `style=short` 且 `alpha_mode=hunt` 默认转 `deep-research + custom short-hunt batch`
  - 其他场景默认保留 `hybrid`
- `hybrid`
  - 适合：先搭框架，再做有限深挖
  - 做法：普通 task session + FinanceMCP + web/fetch，必要时再局部切到其他 skill
- `superpowers`
  - 适合：复杂规划、跨市场比较、需要拆解任务或并发设计
- `deep-research`
  - 适合：需要带引用的正式报告、证据链、历史对照、数值验证

路由原则：

- “先给我筛一批，再说理由” -> `hybrid`，但短线默认不用它
- “做完整深研报告” -> `deep-research`
- “帮我把 long/short 框架设计成可复用策略体系” -> `superpowers`
- “帮我像饿狼一样找 2-15 个交易日前的潜伏买点” -> `deep-research` + `alpha_mode=hunt`
- “美股先行，A股/港股跟随，给我 24-48h 的可执行交易” -> `deep-research` + `alpha_mode=lead-follow`

默认假设：

- 如果用户没有特别说明，默认 `execution_profile=east-asia-cash-hours`
- 这意味着：
  - 可以把美股、商品、美债等当成**信号市场**
  - 但 24-48h 的直接执行标的应优先落在用户更容易操作的市场和时段
- 如果用户没有明确给出 `horizon`，必须根据 `market + style + instrument + execution_profile` 自动推断，并在报告开头写清楚

### 3. 数据获取顺序

坚持这个顺序，避免先被叙事带跑：

1. **FinanceMCP 结构化数据优先**
   - 行情、分钟线、指数、宏观、财务、资金流、龙虎榜、融资融券、基金、可转债
2. **原生 web/fetch 补最新信息**
   - 最新新闻、公告、研报、行业催化、政策变化
3. **已有 workspace 资料复用**
   - 相关历史报告、memory、news、report 中已存在的结果
4. **最后才写叙事**
   - 先表格和评分，再文字结论
5. **task 里必须有真实输出**
   - `agents/*.md` 只是 brief
   - 真正的研究内容应落到：
     - `research/<agent-slug>.md`
     - `research/<agent-slug>.worklog.md`
     - `research/<agent-slug>.raw.json`
     - `reports/*.md`
     - `reports/quant/*`
     - `native-subagents/manifest.json`
     - `native-subagents/prompts/*.md`
   - 调研过程中一旦确认到有价值的事实、来源或结构化结果，就应即时写入 task-local `research/`，不要只留在聊天上下文里等最后汇总

### 3.1 简单建模与回测是硬要求

当任务里出现以下任一内容时，不能只靠嘴说“量化验证”：

- quant verifier
- backtest
- signal strength
- 胜率 / 盈亏比
- 线性模型
- 因子评分
- lead-lag 验证

必须至少完成一项真实计算：

- 因子打分
- 简单线性回归
- forward return 回测

并把这些东西落成 task 内文件：

- `scripts/market-alpha-quant-compass.py`
- `scratch/quant/*.csv`
- `reports/quant/*.json`

如果没有真实脚本输出，就不能在报告里把量化部分写成“已完成”。

### 4. Long 路线

适用于中长线、多因子、宏观驱动、行业景气或价值成长筛选。

最小链路：

1. 宏观和流动性定调
2. 行业/主题优选
3. 指数成分或候选池展开
4. 公司财务与业务质量核验
5. 资金与技术确认
6. 形成交易计划和风险边界

优先工具：

- `macro_econ`
- `index_data`
- `csi_index_constituents`
- `company_performance`
- `company_performance_hk`
- `company_performance_us`
- `fund_data`
- `money_flow`
- `stock_data`
- `finance_news`
- `hot_news_7x24`

### 5. Short 路线

适用于短线、高频代理信号、事件驱动、量价和资金行为筛选。

默认目标不是追逐今天已经上热搜的公开事件，而是提前识别 **2-15 个交易日内仍有爆发概率的潜伏买点**。

先明确两个概念：

- `signal_market`
  - 最先给出风险偏好、产业链、事件催化信号的市场
- `execution_market`
  - 用户真正更容易下单、盯盘、止盈止损的市场

短线 scan 不能把两者混成一回事。

最小链路：

1. **拥挤度过滤先行**
   - 先排除已经被公开事件打满预期的方向
   - 例如：同一主事件 72 小时内头部媒体/研报覆盖过密、RSI 已高企、热搜过热
2. **隐性催化搜索**
   - 找供应链、政策边角、订单、渠道、产品节奏、情绪错配
3. **微观结构验证**
   - 分钟线与日线共振
   - 缩量沉淀后脉冲放量
   - 大盘弱时的逆势承接
4. **资金行为验证**
   - 资金流、龙虎榜、融资融券、大宗交易交叉验证
5. **历史与证伪**
   - 对照历史相似启动形态
   - 主动寻找能否证伪这个买点
6. **输出触发位、失效位、仓位规则**

### 5.0 24-48h 特殊规则

当用户明确要 `24-48h` 或 `1-2天` 机会时：

- 优先寻找 **下一交易时段仍可执行的买点**
- 如果 `signal_market=US` 且 `execution_profile=east-asia-cash-hours`：
  - 默认不要把美股个股本身排成第一执行标的
  - 更合理的输出应是：
    - `US signal -> CN/HK follow trade`
    - 或者 `US signal only, not recommended for direct execution`
- 除非用户明确说可以做美股夜盘或隔夜盯盘，否则不能把需要东亚深夜频繁操作的标的当首选执行方案

例子：

- `NVDA` 更适合作为 `signal_market`
- `兆易创新`、A股算力链、港股相关映射标的，更可能是 `execution_market`

所以 24-48h 报告必须回答：

- 信号从哪里来
- 最佳执行应落在哪个市场
- 这笔交易对用户的作息和盯盘要求是否合理

### 5.2 Lead-Follow 模式

当用户明确要的是：

- “美股先行，A股跟随”
- “海外信号，东亚时段执行”
- “给我 24-48h 的映射交易”

使用：

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-bootstrap.sh \
  --task-slug "<slug>" \
  --market "<us|multi>" \
  --style short \
  --alpha-mode lead-follow \
  --horizon h24-48 \
  --objective "<goal>"
```

这个模式要求：

- 把先行信号市场和跟随执行市场拆开
- 不把先行市场的高拥挤交易，直接当成执行建议
- 重点寻找：
  - `US signal -> CN/HK execution`
  - `macro / commodity signal -> sector / equity execution`
  - `overnight signal -> next cash session trade`

如果用户默认在东亚现金时段交易：

- 美股龙头更适合作为 `signal_market`
- A股 / 港股 / 亚洲时段相关合约更适合作为 `execution_market`

batch 生成后，直接准备原生 subagent 执行计划：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-subagents.py \
  --task-slug "<task-slug>"
```

然后：

- 读 `tasks/.../native-subagents/coordinator-playbook.md`
- 按 wave 使用 OpenClaw 原生 `sessions_spawn` / `/subagents spawn`
- 每次 accepted 后，立刻执行 `manifest.json` 对应 agent 的 `record_spawn_command`
- 需要看进度时，用 `subagents(action=list|info|log|steer|kill)` 按需查看
- 在对外汇报“已启动/已完成”前，先跑：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-coordinator.py \
  status \
  --task-slug "<slug>"
```

- 如果 live tool list 里没有 `sessions_spawn`，必须直接说明 `BLOCKED`，不能伪装成已经并发执行
- 不要把 `market-alpha-run-batch.sh` 当默认路径；它现在只是 legacy fallback

优先工具：

- `stock_data_minutes`
- `stock_data`
- `money_flow`
- `margin_trade`
- `block_trade`
- `dragon_tiger_inst`
- `finance_news`
- `hot_news_7x24`

### 5.1 Short Alpha Hunt 模式

当用户要的是“Alpha 狙击”“潜伏买点”“不要众人皆知的事件后卖点”时，使用：

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-bootstrap.sh \
  --task-slug "<slug>" \
  --market "<cn|us|hk>" \
  --style short \
  --alpha-mode hunt \
  --objective "<goal>"
```

这个模式会：

- 自动把引擎切到 `deep-research`
- 不使用 generic default batch
- 改为生成一组专用 short-hunt agents

这些 agents 的重点不是“解释公开事件”，而是：

- 找未被充分覆盖的催化剂
- 找静默期筹码收集和异常脉冲
- 找市场下跌日里的反直觉相对强势
- 做拥挤度毒丸过滤
- 强制证伪，避免把 exit liquidity 当作买点

具体逻辑见 `references/short-alpha-hunt.md`。

batch 生成后，直接准备原生 subagent 执行计划：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-subagents.py \
  --task-slug "<task-slug>"
```

然后：

- 使用 `tasks/.../native-subagents/manifest.json` 里的 `spawn_task`
- 把 `planner` 作为 wave 0，研究 / quant lanes 并发作为 wave 1
- `synthesis-analyst -> reviewer -> report-generator` 顺序收敛
- 量化或回测任务必须由原生 subagent 在运行时容器内真实执行 `scripts/market-alpha-quant-compass.py`

### 6. 衍生品 / 合约结构路线

适用于期货、期权、可转债或“先有标的观点，再构建合约结构”。

执行原则：

1. 先建立**标的观点**
2. 再选择**合约类型**
3. 最后输出**结构与风险**

现有能力边界：

- 当前 FinanceMCP 已支持：
  - `stock_data` 查询 `futures` / `options` / `convertible_bond`
  - `stock_data_minutes` 查询 `cn` / `crypto` 分钟线
  - 指数、宏观、新闻、财务、资金流等底层信息
- 当前未看到专门的：
  - 期权链
  - Greeks
  - IV / skew / OI
  - 美股期权专用链路

所以当用户要求“美股衍生品合约类型”时：

- 可以输出：
  - underlying thesis
  - directional bias
  - 推荐结构类型（如 call spread / put spread / collar / covered call）
  - 触发条件、失效条件、风险预算
- 必须同时明确：
  - 当前缺失哪些链路数据
  - 哪些结论是结构建议，不是基于完整期权链优化后的精确执行单

## 输出合同

### 选股结果最少要有

- 一句话结论
- 候选池表格
- 每个标的的核心逻辑
- 风险与失效条件
- 下一步动作

### 深研结果最少要有

- 研究问题
- 证据链
- 内在逻辑
- 风险矩阵
- 交易计划
- `Bot Handoff` JSON
- 还缺什么数据
- 若使用量化验证，则必须追加 `Quant Evidence`
- 若用户要求全量交付，则必须提供 task package 路径和发送提示
- 如果某条搜索结果无法映射到 `候选逻辑 / 入场触发 / 风险失效 / 数据缺口` 四类之一，就不要堆进最终报告

### 交易计划最少要有

- 方向：做多 / 做空 / 观望 / 结构性
- 时间框架：日内 / 1-5 日 / 1-3 月 / 6-12 月
- 策略标签：如 `pre-consensus-buy` / `lead-follow` / `mean-reversion`
- 入场触发
- 入场区间
- 订单类型：limit / ladder / stop-limit / market-on-breakout
- 加仓条件
- 减仓条件
- 止盈梯度：至少 `T1 / T2`
- 动态止损 / 跟踪止损
- 时间止损
- 止损 / 失效条件
- 仓位建议
- 滑点预算 / 流动性约束
- 风险收益比估算
- 进入周期 / 退出周期
- 最大持有时长
- 特殊情况调整规则
- 若数据不足，必须明确标记 `NOT_EXECUTABLE`，而不是假装给出可交易建议

不要只输出“推荐理由”。必须落到可执行计划。

### Bot Handoff 最少要有

- 固定 section 名：`## Bot Handoff`
- 固定使用 fenced `json` 代码块
- 用于 Rust / 规则引擎消费的最少字段：
  - `ticker`
  - `direction`
  - `entry_trigger`
  - `entry_zone`
  - `order_type`
  - `stop_loss`
  - `take_profit`
  - `time_stop`
  - `max_holding_period`
  - `invalidation`
- 若当前研究不足以形成可执行策略，输出：
  - `status: NOT_EXECUTABLE`
  - `reason`
  - `missing_fields`

短线额外必须回答：

- 这是 **潜伏买点** 还是 **拥挤事件交易**
- 如果是拥挤事件交易，是否应降级为 `volatility-only`
- 为什么它还有 Alpha，而不是给别人接盘
- `signal_market` 是什么，`execution_market` 是什么
- 对当前用户是否属于 `native-hours` / `overnight-manageable` / `not-recommended`
- 当前策略的默认进入窗口、退出窗口、最晚失效时间是什么
- 固定增加 `## Data Freshness & Completeness`
- 对每个金融高时效任务标记：
  - `Market data as of`
  - `News data as of`
  - `Options data as of`
  - `Options data status`
  - `Timeline span`
  - `Completeness status`
  - `Precision level`
  - `Critical missing fields`
  - `Fallback sources used`
- 若声称做过量化验证，必须给：
  - script path
  - input data path
  - output json path
  - 使用的方法（score / regress / backtest-forward）
  - score/backtest 的一句话摘要

## 报告与交付

最终报告不要直接手写到 `workspace/report/` 一个随意名字。

统一用：

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-deliver.sh \
  --path "<draft-report>" \
  --task-slug "<task-slug>"
```

这个脚本负责：

- 尽量把报告归一到 `generated-report-market-alpha` 命名风格
- 复用 `workspace/scripts/deliver-report.sh`
- 先通过 `market-alpha-report-gate.py`
- 输出可直接交付的 `FILEPATH:./...`
- 同时输出对应 task 的 `TASK_PATH:./tasks/...`
- 额外打印 `feishu_send_file` 的建议 payload

飞书发送规则：

- 若当前会话可直接用 `feishu_send_file`，优先发送文件
- 最终给用户的飞书文字回复里，至少同时带上：
  - `FILEPATH:./report/...`
  - `TASK_PATH:./tasks/...`
- 如果还生成了 task bundle，也把 bundle 路径一起写上

## 硬约束

- 不要把泛化 prompt 当成最终产物；最终产物必须是“研究编排 + 数据路径 + 报告闭环”
- 不要先写长免责声明再分析
- 不要把 long 和 short 的评分逻辑混成一锅
- 不要假装当前 MCP 已有期权链或 Greeks
- 对短线，不要默认围绕“今天最火”的公开主事件建多头计划
- 遇到预期打满、覆盖过密、价格已过度透支的事件，默认降级为 `crowded-event` 或 `volatility-only`
- 对 `24-48h` 报告，不要把“需要用户在东亚深夜高强度盯盘的美股单名交易”默认排到第一执行位
- 如果用户未指定周期，不允许把报告做成“没有明确持有时长”的模糊交易建议
- 不允许在没有脚本和结果文件的情况下，把 agent 写成“已完成回测 / 已完成量化验证”
- 若报告自己承认“无法推荐具体行权价 / 到期日 / 技术指标缺失 / 实时价格缺失 / 期权链缺失”，则必须同步降级为：
  - `DIRECTIONAL_ONLY`
  - `WATCHLIST`
  - `NOT_EXECUTABLE`
- 对每个结论都标记：
  - `事实`
  - `推断`
  - `缺口`

## 推荐配套

- 复杂设计任务：联动 `superpowers`
- 引用型深研：联动 `deep-research`
- 文件发送：联动 `feishu-file-transfer`
- 最新新闻补证：联动 `network-search` 或原生 web/fetch
