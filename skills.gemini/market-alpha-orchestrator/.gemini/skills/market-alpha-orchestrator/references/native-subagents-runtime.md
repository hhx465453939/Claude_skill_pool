# Native Subagents Runtime

这是 market-alpha 在 OpenClaw 里的默认并发执行路径。

目标：

- 继续复用 task session / capsule / agent brief
- 但真正的多 agent 执行交给 OpenClaw 原生 `sessions_spawn` / `/subagents`
- 不再把外置 `market-alpha-agent-runner.py` 当主路径

## 主路径

1. 先建 task，并生成 `agents/*.md`
2. 运行：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-subagents.py \
  --task-slug "<slug>"
```

3. 读取：
   - `tasks/.../native-subagents/manifest.json`
   - `tasks/.../native-subagents/coordinator-playbook.md`
   - `tasks/.../native-subagents/prompts/*.md`
4. 先验证 bridge：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-coordinator.py \
  validate \
  --task-slug "<slug>"
```

5. 主 agent 使用原生 `sessions_spawn` 或 `/subagents spawn` 启动各 lane
6. 每次 `sessions_spawn` accepted 后，立刻运行该 agent 在 `manifest.json` 里的 `record_spawn_command`
7. 波次之间用下面的状态快照确认真实进度，而不是口头假设：

```bash
python3 workspace/skills/market-alpha-orchestrator/scripts/market-alpha-native-coordinator.py \
  status \
  --task-slug "<slug>"
```

## 为什么用原生 subagents

- OpenClaw 原生会给每个子 agent 一个独立 session
- 完成后可通过 announce / `subagents list|log|info|steer|kill` 管理
- 不需要再额外包一层 Python thread runner
- task 内仍保留 `research/*.md`、`research/*.worklog.md`、`research/*.raw.json`

## 协调规则

- `planner`：优先跑，产出依赖图或约束收敛
- 研究 lane：并发跑
- `synthesis-analyst`：在研究 lane 基本完成后收敛
- `reviewer`：在 synthesis 之后做质量阻断
- `report-generator`：最后产出正式候选稿
- 不得在没有 `sessions_spawn` receipt 的情况下宣称某个 wave “已启动”
- 不得在 `agents.jsonl` / `research/*.worklog.md` / `reports/quant/*` 没有对应落盘时宣称某个 wave “已完成”
- 若 live tool list 里没有 `sessions_spawn`，应明确输出 `BLOCKED`，而不是假装已经在并发执行

## 量化 / 回测规则

如果 brief 涉及：

- score
- regress
- lead-lag
- backtest
- win rate / payoff ratio

则 `quant-verifier` 必须在 OpenClaw runtime 容器内真实执行：

- `tasks/.../scripts/market-alpha-quant-compass.py`
- `tasks/.../scratch/quant/*.csv`
- `tasks/.../reports/quant/*.json|csv|png`

最小链路：

```bash
python3 tasks/.../scripts/market-alpha-quant-compass.py detect-runtime --output tasks/.../reports/quant/runtime-profile.json
python3 tasks/.../scripts/market-alpha-quant-compass.py choose-model --rows 200 --features 6 --horizon <horizon> --target-type continuous --output tasks/.../reports/quant/model-router.json
python3 tasks/.../scripts/market-alpha-quant-compass.py score --input tasks/.../scratch/quant/candidate-factors.csv --factors signal_strength:0.35,relative_strength:0.25,turnover_pulse:0.20,flow_confirmation:0.30,crowding_penalty:-0.30 --top 10 --output tasks/.../reports/quant/factor-score.json
python3 tasks/.../scripts/market-alpha-quant-compass.py backtest-forward --input tasks/.../scratch/quant/signal-backtest.csv --signal-col signal --horizons 1,2,3,5 --output tasks/.../reports/quant/backtest-summary.json
```

注意：

- 如果输入仍是模板行（如 `ticker=EXAMPLE`），不能声称“量化验证已完成”
- 必须先填真实输入，或明确输出 `BLOCKED`

## FinanceMCP 规则

- 必须先验证，不要臆测
- 当前 `repo/docker-compose.yml` 已挂载 `/mnt/500G-1/Development`
- 因此 `finance-mcp-local` / `tavily-mcp-local` 这类指向 `/mnt/500G-1/Development/...` 的入口，在 compose reload 后应当容器内可见
- 若文件已可见但工具仍失败，继续排查 server 启动或调用方式
- 不允许臆造 `localhost:3000/mcp/...` 这类未证实的调用路径
- 正确做法：
  - 先检查容器内文件是否存在
  - 再决定使用 MCP、修 server 调用，还是降级到其他数据源

## 可观测性

- 任务级：`agents.jsonl`
- 研究级：`research/*.worklog.md`
- 量化级：`reports/quant/*`
- 运行级：OpenClaw 原生 `subagents` 工具

## 旧 runner

`market-alpha-run-batch.sh` / `market-alpha-agent-runner.py` 现在只保留为 fallback：

- 当原生 `sessions_spawn` 真不可用时才考虑
- 不能再作为默认主路径写进执行说明
