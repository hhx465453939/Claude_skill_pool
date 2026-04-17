# Quant Compass

这是 market-alpha 的轻量量化罗盘，不是全功能策略研究平台。

它的目标是把“量化验证”从一句空话，变成 task 内真实存在的脚本与结果文件。

## 提供的能力

### 0. 运行时检测与模型路由

输入：

- 当前机器运行时
- 数据行数
- 特征数
- horizon
- target type

输出：

- `runtime-profile.json`
- `model-router.json`

适合：

- 自动判断当前是 `lightweight-cpu` / `balanced-cpu` / `gpu-accelerated`
- 在不改脚本的情况下，为未来 GPU 主机提供升级路径
- 为当前任务选择更合适的轻量 / 中量模型族

### 1. 因子打分

输入：

- `candidate-factors.csv`
- 或等价 JSON

输出：

- 标准化 z-score 后的 `alpha_score`
- 每个因子的贡献

适合：

- 候选池排序
- signal strength 评分
- crowding penalty 合并

### 1.5 多因子共振

输入：

- `candidate-factors.csv`
- 因子权重定义

输出：

- `resonance_score`
- `aligned_factors`
- `conflicting_factors`
- JSON / CSV / PNG

适合：

- 看一组因子是否在同一方向共振
- 区分“高分但冲突多”与“高分且一致性高”的候选

### 1.6 因子挖掘

输入：

- 带目标列的因子数据表
- 目标列如 `forward_return` / `future_return`

输出：

- 单因子相关性
- 分桶 spread
- 单调性
- `mine_score`
- JSON / CSV / PNG

适合：

- 从 task-local 数据里快速发现更有用的候选因子
- 给 strategy lab 提供候选因子排序，而不是只凭直觉堆指标

### 2. 简单线性回归

输入：

- 两列数值数据

输出：

- slope
- intercept
- correlation
- r_squared
- rmse

适合：

- lead-lag 粗验证
- 因子与未来收益的简单线性关系验证

### 3. forward return 回测

输入：

- `signal-backtest.csv`
- 至少包含 `close`
- 可选 `signal`

输出：

- 不同 horizon 的：
  - trade count
  - avg_return
  - median_return
  - hit_rate
  - payoff_ratio
  - max_drawdown

适合：

- 24-48h / 3-7d / 1-2w 的简易信号回测

### 4. 分桶评估

输入：

- 一个因子列
- 一个未来收益列

输出：

- 不同 bucket 的平均收益
- hit rate
- CSV / PNG

适合：

- 判断因子单调性
- 快速验证一个因子是否真有方向性

### 5. lead-lag 扫描

输入：

- `x` 列
- `y` 列
- 最大滞后步数

输出：

- 不同 lag 的 correlation / r_squared / slope
- 最优 lag
- CSV / PNG

适合：

- lead-follow 验证
- 跨市场信号传导的粗测

## 运行时适配

### lightweight-cpu

适用当前这类机器：

- 无 GPU
- 内存约 8GB
- 老 CPU / NAS / Docker 轻量容器

推荐能力：

- linear score
- OLS regression
- bucket eval
- lead-lag scan
- forward backtest

### balanced-cpu

适合：

- 无 GPU
- 但 CPU 核数、内存更宽裕

推荐能力：

- 在 lightweight-cpu 基础上
- 增加 bootstrap / grid-search / 更大样本扫描

### gpu-accelerated

适合：

- 有 NVIDIA GPU
- 具备后续扩展 torch / tree model 的环境

推荐能力：

- 当前脚本仍先跑轻量基线
- 再根据需要升级到更复杂模型

关键点：

- 不需要改 reference 或工作流
- 只是 runtime profile 和 model router 会给出不同建议

## 不提供的能力

- 高频 tick 级回测
- 订单簿撮合模拟
- 复杂期权 Greeks
- 组合优化器
- 重型 pandas / numpy / sklearn 研究环境

如果这些是刚需，应升级到专门的量化研究环境，而不是继续滥用这个脚本。

## 文件落点

初始化后，task 内应该出现：

- `scripts/market-alpha-quant-compass.py`
- `scratch/quant/candidate-factors.csv`
- `scratch/quant/signal-backtest.csv`
- `reports/quant/runtime-profile.json`
- `reports/quant/model-router.json`
- `reports/quant/*.json`
- `native-subagents/prompts/quant-verifier.md`

## 与 OpenClaw 原生子 agent 的结合

默认主路径不是外置 Python runner，而是：

- 主 agent 先读取 `native-subagents/coordinator-playbook.md`
- 再使用 OpenClaw 原生 `sessions_spawn` / `/subagents`
- `quant-verifier` 子 agent 在运行时容器内真实执行本脚本

这意味着：

- `detect-runtime`
- `choose-model`
- `score`
- `resonance`
- `factor-mine`
- `backtest-forward`

都应由原生 subagent 通过本地 `exec` 实际跑出文件，而不是只在报告里口头引用。

## 报告引用规范

报告中若使用量化结论，至少引用：

- script path
- input path
- output path
- 使用的命令

否则不要写“已量化验证”。
