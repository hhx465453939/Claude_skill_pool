# Runtime Discipline

## 真实任务禁止事项

- 不要读取任何历史 smoke task 作为当前任务上下文。
- 不要假定 `short-alpha-general-smoke` 或 `short-alpha-general-us-smoke` 是当前 task。
- 当前 task 的唯一来源应是：
  - 当前用户请求
  - 当前 bootstrap 生成的 task 目录
  - 当前 task 内的 `TASK_ORCHESTRATION.md`

## 并发梯度

遇到模型供应商限速、timeout、quota、tool-use 中断时：

- 先停止扩张并发
- 自动按梯度降级：
  - `6 -> 4 -> 2 -> 1`
- 若 `1` 仍失败：
  - 进入 `parent-only`
  - 主 agent 单线程串行推进整个任务

## 原则

- 不允许因为 GLM/ZAI 限速就让任务停在半空
- 最差也必须进入 `single-thread battle mode`
- 不能把“限速”当作交付中断的理由，只能当作调度模式切换的触发器
