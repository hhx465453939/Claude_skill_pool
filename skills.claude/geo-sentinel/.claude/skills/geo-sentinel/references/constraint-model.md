# Constraint Model Reference

## Why F-G Needed an Upgrade

旧版 F-G 的核心问题不是“有约束”这件事，而是约束方式过于单一：

- 单一全局基准率会把所有场景硬塞进同一个锚点
- 线性混合容易把强反证、弱基准率和时间窗口压扁成一个平均数
- 默认围绕 `0.5` 附近直觉极值化，容易忽略 reference class
- 置信区间更多像 heuristic clamp，而不是围绕真实不确定性的近似

因此新版升级为 `F-G+`：

- `F`: 多场景推理，可选 low-cost inner-crowd
- `G`: 基准率锚定 + 驱动拆解 + 反证校准 + 先验感知再校准 + tail discipline

## Core Formula

对每个场景 `i`：

```text
P_base(i)    = 该场景 reference class 基准率
P_llm(i)     = 单次或多次 reasoning frame 聚合后的中心概率
S(i)         = 支持 / 反对信号平衡分数，范围 [-1, 1]
A(i)         = 历史类比分数，范围 [-1, 1]
P_anchor(i)  = 先验锚点；优先取估计先验，否则回落到 P_base(i)
gamma(i)     = 极值化 / 去极值化系数，围绕锚点做，而不是围绕 0.5
```

先做一轮 logit-space 混合：

```text
logit(P_mix(i)) =
    α · logit(P_base(i)) +
    β · logit(P_llm(i)) +
    γ · (signal_scale · S(i)) +
    δ · (analogue_scale · A(i))
```

默认参数：

- `α = 0.40`
- `β = 0.35`
- `γ = 0.15`
- `δ = 0.10`
- `signal_scale = 1.60`
- `analogue_scale = 1.20`

然后围绕先验锚点做再校准：

```text
P_recal(i) =
    sigmoid(
        logit(P_anchor(i)) +
        gamma(i) · (logit(P_mix(i)) - logit(P_anchor(i)))
    )
```

解释：

- 若 `gamma(i) > 1`，表示在信息相对独立、存在有效少数派信号时，允许适度极值化
- 若 `gamma(i) < 1`，表示信息高度重叠、证据薄弱、时间跨度太长时，应去极值化
- 关键点是：**极值化围绕锚点，而不是机械围绕 0.5**

## Low-Cost Inner-Crowd Aggregation

若一个场景存在多个 reasoning frame 的概率估计：

```text
P_llm(i) = median(llm_probabilities(i))
dispersion(i) = mean(|p_k - median(p)|)
skew(i) = mean(p_k) - median(p)
```

用途：

- `median` 比简单均值更抗异常值
- `dispersion` 越大，区间越宽
- 在有少数派强烈异议时，可以触发轻微 contrarian bonus，但不会无约束放大

## Tail Discipline

对于极低基准率场景，如果支持信号和历史类比都不够强，则执行 soft cap：

```text
if P_base(i) < 0.10 and S(i) < 0.20 and A(i) < 0.20:
    P_recal(i) <= min(max(3 * P_base(i), 1.15 * P_llm(i), 0.02), 0.35)
```

目的：

- 阻止模型把“历史上极少发生”的事件轻易推到高概率
- 但保留在异常强证据下向上修正的空间

## Uncertainty Bands

基础 sigma 仍按事件类别区分，但新版把它更多用于**区间宽度**，而不是直接当硬 clamp。

### Base sigma lookup

| Category | Base sigma | Notes |
|---|---|---|
| Military conflict escalation | 0.15 | High inherent uncertainty |
| Election outcomes | 0.10 | Polls provide some signal |
| Policy/regulation changes | 0.12 | Moderate predictability |
| Trade/economic decisions | 0.08 | More constrained by economics |
| Diplomatic negotiations | 0.13 | Actor-dependent variance |
| Regime change | 0.18 | Rare, high variance |
| Market-moving events | 0.11 | Partially priced in |
| default | 0.14 | Fallback |

调整方式：

```text
sigma(i) =
    sigma_base(category) *
    (1 + 0.05 · n_conflicting) *
    (1 + 0.004 · t_days) *
    (1 + 1.50 · dispersion(i)) *
    (1 + 0.50 · shared_information_risk) *
    (1 + 0.50 · (1 - reference_quality(i)))
```

其中：

- `n_conflicting`: 冲突信号数
- `t_days`: 预测窗口天数
- `dispersion(i)`: inner-crowd 离散度
- `shared_information_risk`: 信息重叠风险，默认 `0.35`
- `reference_quality(i)`: 参考类质量，基于样本量和可比性，范围 `[0, 1]`

区间半宽：

```text
ci_half(i) = min(0.35, 1.96 · sigma(i) · 0.45)
```

因此：

```text
CI(i) = [max(0, P(i) - ci_half(i)), min(1, P(i) + ci_half(i))]
```

## Gamma Heuristic

`gamma(i)` 不再固定。它由以下因素轻量决定：

```text
gamma(i) =
    clamp(
        1.0
        + diversity_bonus(i)
        + contrarian_bonus(i)
        + 0.10 · (reference_quality(i) - 0.50)
        - 0.35 · shared_information_risk,
        0.85,
        1.35
    )
```

其中：

- `diversity_bonus`: 来自多 reasoning frame 的离散度和轻微偏斜
- `contrarian_bonus`: 少数派但有证据支撑时的轻微加成
- `shared_information_risk`: 若所有推理都来自同一堆素材，则压低 gamma

## Convergence

引擎默认做 `2-3` 次轻量迭代：

1. 用原始场景概率做第一轮约束
2. 归一化后把结果作为下一轮的 working prior
3. 若最大概率变化量 `< threshold`，则收敛

默认：

- `max_iter = 3`
- `threshold = 0.03`

## Practical Guidance

- 没有 scenario-specific base rate 时，至少给 event family 一个 base rate，再均分到场景层，避免完全无锚。
- 若只有单次 LLM 概率，没有 inner-crowd，也可以正常运行，只是 `gamma` 会更保守。
- 若没有可靠历史类比，不要编造 analogue score；宁可让不确定性变宽。
- 若未来能回收真实结果，推荐把 task 的最终概率与真实 outcome 写回校准账本，后续用 Brier / log score 回看。
