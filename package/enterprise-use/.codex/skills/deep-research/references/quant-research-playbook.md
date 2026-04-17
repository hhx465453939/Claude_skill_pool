# Deep Research Quant Playbook

## 适用场景

当研究问题包含以下任一特征时，进入轻量量化验证模式：

- 涉及利率、通胀、汇率、股价、估值、财务比率、增长率
- 涉及“是否显著上升/下降”“趋势是否成立”“相关性是否存在”
- 涉及样本对比、时间序列、基础预测、政策变量对结果变量的影响
- 用户明确要求“算一下”“建个简单模型”“用数据验证”

## 原则

- 先求可验证，再求复杂
- 优先做能解释得清楚的简单模型，而不是追求高级模型名词
- 没有足够样本时，不要过度建模
- 所有数值结论都要带上数据来源、时间范围、样本量、局限性

## 推荐工作流

### 1. 定义数值问题

- 要验证什么结论？
- 因变量和自变量是什么？
- 时间范围是什么？
- 是否只需要描述统计，还是需要一个简单趋势/回归？

### 2. 获取数据

优先级：

1. 官方公开数据
2. 论文附录 / 数据库导出
3. 机构报告中的表格或 CSV
4. 新闻报道中的数字，仅用于线索，不直接当正式样本

对于固定公开时间序列，可直接用：

```bash
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py fetch-fred \
  --series FEDFUNDS \
  --start 2015-01-01 \
  --output workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/fedfunds.csv
```

常用 FRED 例子：

- `FEDFUNDS`: Effective Federal Funds Rate
- `CPIAUCSL`: CPI for All Urban Consumers
- `UNRATE`: Unemployment Rate
- `DGS10`: 10-Year Treasury Constant Maturity Rate

### 3. 做最小验证

#### 只需要摘要统计时

```bash
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py describe \
  --input workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/fedfunds.csv \
  --column value
```

#### 只需要验证简单线性关系时

准备一个清洗过的 CSV，至少包含两列：`x` 和 `y`

```bash
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py regress \
  --input workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/sample.csv \
  --x x \
  --y y \
  --json
```

输出重点关注：

- `slope`
- `correlation`
- `r_squared`
- `rmse`
- `observations`

#### 只需要核算公式时

```bash
python3 workspace/skills/deep-research/scripts/research_quant_toolkit.py calc \
  --expr "(new-old)/old*100" \
  --var old=5.25 \
  --var new=4.50
```

### 4. 写回报告

报告中必须写清：

- 数据来源
- 时间范围
- 样本量
- 方法是“描述统计 / 简单线性回归 / 公式核算”
- 结果如何支持或不支持原命题
- 局限性是什么

## Temp Script 规则

- 临时脚本优先放到 `workspace/tasks/YYYY-MM-DD-<task-slug>/scratch/`
- 文件名建议：`YYYY-MM-DD-<topic>-analysis.py`
- 优先从 `quant_scratchpad_template.py` 复制
- 任务结束后保留有价值的 scratch 脚本；一次性垃圾脚本可以删除

## 不该做什么

- 不要在样本量极小、定义不清时硬上复杂回归
- 不要把相关性直接写成因果性
- 不要只贴脚本输出，不解释含义
- 不要只引用二手媒体数字而不核对原始来源
