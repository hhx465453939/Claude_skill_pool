# Reporting And Delivery

## 原则

- 复杂任务先放 task session
- 报告先成稿，再统一交付
- 不手写随机报告名

## 推荐路径

### 1. 建 task

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-bootstrap.sh \
  --task-slug "<slug>" \
  --engine "<hybrid|superpowers|deep-research>" \
  --market "<market>" \
  --style "<style>" \
  --objective "<goal>"
```

### 2. 在 task 内产出草稿

草稿优先放：

- `tasks/.../reports/`
- `tasks/.../research/`
- `tasks/.../scratch/`
- `tasks/.../native-subagents/`

对于 short-hunt / lead-follow：

- 每个 agent 都应优先把自己的结果写到：
  - `tasks/.../research/<agent-slug>.md`
  - `tasks/.../research/<agent-slug>.worklog.md`
  - `tasks/.../research/<agent-slug>.raw.json`
  - `tasks/.../native-subagents/manifest.json`
  - `tasks/.../native-subagents/prompts/<agent-slug>.md`

不要只有 `agents/brief.md`，却没有真实 research 输出。

原生并发主路径：

- 先运行 `market-alpha-native-subagents.py`
- 让主 agent 读取 `native-subagents/coordinator-playbook.md`
- 再用 OpenClaw 原生 `sessions_spawn` / `/subagents` 启动各 lane
- `market-alpha-run-batch.sh` 只能作为 fallback，不再是默认执行路径

执行建议：

- worker 一旦确认到可复用事实、来源链接、候选筛选结果，就立刻写入 `research/*.worklog.md`
- 结构化或机器可消费的中间结果优先写入 `research/*.raw.json`
- 最终报告只做清洗和汇总，不承担“唯一记忆体”角色
- native subagent 应在开始 / 完成时把状态回写 `agents.jsonl`

### 3. 交付正式报告

```bash
bash workspace/skills/market-alpha-orchestrator/scripts/market-alpha-deliver.sh \
  --path "<draft-report>" \
  --task-slug "<slug>"
```

这个脚本在正式交付前会先跑质量闸门：

- 检查最小报告结构
- 检查 quant claim 是否带 `Quant Evidence`
- 检查 task 是否真的有研究输出，而不是只有 queued briefs
- 输出正式报告路径和对应 task 路径，方便用户回看 task 内证据

### 4. 发送到飞书

优先：

```json
{
  "action": "upload_and_send",
  "file_path": "report/<final-file>.md"
}
```

如果当前回合不能直接调工具，至少输出：

```text
FILEPATH:./report/<final-file>.md
TASK_PATH:./tasks/<task-dir>
```

即使已经成功发送文件，最终飞书文字回复里也应保留 `TASK_PATH:./tasks/<task-dir>`，方便用户继续本地复盘、复用脚本和检查中间产物。

### 5. 可选打包整个 task

如果用户明确要求“把整个 task 发给我 / 打包给我 / 连同脚本和中间证据一起发”：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-package-task.py \
  --task-slug "<slug>" \
  --include-scratch
```

这个脚本会：

- 生成 task zip
- 记录到 `artifacts.jsonl`
- 打印 `feishu_send_file` payload
- 保留 task 目录本身的路径，供文字回复同步给用户

默认打包：

- `README.md`
- `meta.json`
- `capsules/`
- `agents/`
- `reports/`
- `scripts/`
- 各种 `*.jsonl`

可选：

- `--include-scratch`
- `--include-sources`

## 命名预期

最终名尽量落到：

```text
<timestamp>-<task-slug>-generated-report-market-alpha.md
```

## 最终报告最低结构

- 执行摘要
- 市场 / 风格 / 时间框架
- Data Freshness & Completeness
- 事件驱动因子
- 候选池或目标标的
- 核心逻辑
- 风险矩阵
- 交易计划
- Bot Handoff
- 数据缺口

对于 truth-first / hunt / derivatives-sensitive 任务，还应同时有：

- task-local `underlying-truth-ledger.json`
- task-local `reviewer-verdict.json`
- 若存在重复模式，则至少一份 task-local strategy lab 输出

## 交易计划最低字段

每个可执行标的至少给出：

- `方向`
- `策略标签`
- `入场触发`
- `入场区间`
- `订单类型`
- `加仓条件`
- `减仓条件`
- `止盈目标位`（至少 T1 / T2）
- `动态止损` 或明确写 `none`
- `时间止损`
- `核心止损位`
- `失效条件`
- `仓位建议`
- `最大持有时长`
- `流动性 / 滑点约束`

如果这些字段缺失，就不要把它写成“可执行交易建议”；应明确标记为 `NOT_EXECUTABLE`。

## Data Freshness And Completeness（金融高时效任务必选）

固定 section：

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

规则：

- `Precision level=EXECUTABLE` 时，`Completeness status` 必须为 `COMPLETE`
- 期权任务若 `Options data status != COMPLETE`，不得输出 precise strike / expiry
- 如果报告正文承认“期权链缺失 / 实时价格缺失 / 技术指标缺失 / 模板量化”，则最终精度必须同步降级
- 如果没有 `reports/derivatives/underlying-truth-ledger.json`，不要把 spot truth 说成已验证
- 如果没有 `reports/review/reviewer-verdict.json`，不要进入正式交付
- 对 `3个月` 左右的美股 hunt，若 reviewer 判定 `NO_SINGLE_NAME_PASSED`，报告必须显式把 ETF 标为 degraded fallback，而不是默认主结论

同时遵守一个压缩原则：

- 搜到的事实如果不能落到 `候选逻辑 / 入场触发 / 风险失效 / 数据缺口`，不要塞进最终报告。

## Quant Evidence（若使用量化验证则必选）

如果报告里出现：

- 技术评分
- 因子打分
- 胜率
- 盈亏比
- 回测
- 线性模型

则最终报告必须新增一个独立小节：

```markdown
## Quant Evidence

- Script path: `tasks/.../scripts/market-alpha-quant-compass.py`
- Input path:
  - `tasks/.../scratch/quant/candidate-factors.csv`
  - `tasks/.../scratch/quant/signal-backtest.csv`
- Output path:
  - `tasks/.../reports/quant/factor-score.json`
  - `tasks/.../reports/quant/backtest-summary.json`
- Method used:
  - `score`
  - `regress`
  - `backtest-forward`
- Summary:
  - top score highlights
  - horizon-level hit rate / avg return / payoff ratio
```

不要只写“量化验证通过”。

必须给文件路径和最小摘要。

## Bot Handoff（面向 Rust / 自动化执行）

最终报告必须带一个固定 section：

````markdown
## Bot Handoff

```json
{
  "status": "EXECUTABLE",
  "task_path": "./tasks/<task-dir>",
  "plans": [
    {
      "ticker": "000001.SZ",
      "direction": "long",
      "entry_trigger": "...",
      "entry_zone": {"min": 10.1, "max": 10.4, "unit": "CNY"},
      "order_type": "limit-ladder",
      "stop_loss": {"price": 9.8, "type": "hard"},
      "take_profit": [
        {"label": "T1", "price": 10.9},
        {"label": "T2", "price": 11.5}
      ],
      "time_stop": "T+2 14:30",
      "max_holding_period": "2 trading days",
      "invalidation": "..."
    }
  ]
}
```
````

如果无法形成可执行计划，仍要输出 `## Bot Handoff`，但内容应改为：

```json
{
  "status": "NOT_EXECUTABLE",
  "reason": "...",
  "missing_fields": ["realtime_price", "liquidity_check"]
}
```
