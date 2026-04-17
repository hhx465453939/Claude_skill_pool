# Short Alpha General

`short-alpha-general` 是一个短周期战役型交易将军 skill。

它不是：

- 通用 market research skill
- HFT / 毫秒级低延迟系统
- 单纯的因子打分器

它是：

- 短周期庙算层
- 道天地将法漏斗层
- OODA 战争循环层
- 容量梯度部署层
- 单名股 short-horizon command layer

## 与现有 skill 的关系

- `market-alpha-orchestrator`
  - 朝廷 / 帅
  - 负责数据层、后勤、task scaffold、交付
- `short-alpha-general`
  - 将
  - 负责 regime、timing、terrain、fertility、campaign score、deployment tier
- `deep-research`
  - 重证据 / 重引用 / 重反证
- `superpowers`
  - 多战场 campaign 设计
- `executive-consultant`
  - `道` 层抽象与大势框架

## 当前开发状态

- 已完成生产级规格（归档于 `workspace/.debug/short-alpha-general-build/SPEC.md`）
- 已完成 skill manifest 与 bootstrap 骨架
- 已完成 doctrine / deployment / OODA / packaging / runtime guard 骨架

## 真实运行规则

- 真实用户任务必须先 bootstrap 当前 task
- 之后只读当前 task 的 `TASK_ORCHESTRATION.md`
- 不要把任何 `short-alpha-general-smoke` task 当作真实运行上下文
- 遇到供应商限速时，按并发梯度自动降级：
  - `6 -> 4 -> 2 -> 1`
  - 若仍失败，进入 `parent-only`，由主 agent 单线程推进

## 搜索交规

- 这个 skill 必须硬遵守：
  - `workspace/SEARCH_RUNTIME.md`
- 金融/宏观/市场检索默认顺序：
  - `finance-mcp -> open-websearch -> zhipu -> metaso -> tavily -> brave`
- 对泛化网页/一般市场信息：
  - 第一跳必须优先 `open-websearch`
- 不要直接把 Brave-backed 原生 `web_search` 当起手式
- `brave` 和 `tavily` 只作为高成本升级层，不是默认主路
