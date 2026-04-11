# TDD 检查清单 🧪

## 在实现任何功能之前，使用此清单

---

## 🚨 停止并重新开始的红旗

如果你遇到以下任何情况，**停止并从 TDD 重新开始**：

- [ ] 在测试之前编写代码
- [ ] 在实现之后编写测试
- [ ] 测试立即通过
- [ ] 无法解释为什么测试失败
- [ ] 测试"稍后"添加
- [ ] 合理化"就这一次"
- [ ] "我已经手动测试过了"
- [ ] "测试后达到相同的目的"
- [ ] "这是关于精神而不是仪式"
- [ ] "作为参考保留"或"调整现有代码"
- [ ] "已经花了 X 小时，删除是浪费的"
- [ ] "TDD 是教条的，我是务实的"
- [ ] "这是不同的，因为..."

**所有这些都意味着：删除代码。从 TDD 重新开始。**

---

## ✅ 完成前验证清单

在将工作标记为完成之前，检查每一项：

- [ ] 每个新函数/方法都有一个测试
- [ ] 在实现之前观察每个测试失败
- [ ] 每个测试都因预期原因失败（功能缺失，而不是拼写错误）
- [ ] 编写了最少的代码来通过每个测试
- [ ] 所有测试通过
- [ ] 输出干净（没有错误、警告）
- [ ] 测试使用真实代码（仅在不可避免时使用 mocks）
- [ ] 边缘情况和错误已覆盖

**无法检查所有框？你跳过了 TDD。重新开始。**

---

## 🔄 RED-GREEN-REFACTOR 循环检查清单

### RED - 编写失败的测试

- [ ] 测试名称清晰且描述行为
- [ ] 测试一个行为（没有"和"）
- [ ] 测试真实代码（仅在不可避免时使用 mocks）
- [ ] 测试展示所需的 API

**好的测试示例**：
```python
test('重试失败的操作 3 次', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };

  const result = await retryOperation(operation);

  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

**坏的测试示例**：
```python
test('重试有效', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(3);
});
```

---

### 验证 RED - 看它失败

- [ ] **强制执行。不要跳过。**
- [ ] 运行测试：`pytest path/to/test.test.ts`（或适当的命令）
- [ ] 确认测试失败（不是错误）
- [ ] 确认失败消息符合预期
- [ ] 确认失败是因为功能缺失（不是拼写错误）

**测试通过？** 你正在测试现有行为。修复测试。

**测试错误？** 修复错误，重新运行直到它正确失败。

---

### GREEN - 最小代码

- [ ] 编写最简单的代码来通过测试
- [ ] 不添加功能
- [ ] 不重构其他代码
- [ ] 不"改进"超出测试

**好的实现示例**：
```python
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === 2) throw e;
    }
  }
  throw new Error('unreachable');
}
```

**坏的实现示例**：
```python
async function retryOperation<T>(
  fn: () => Promise<T>,
  options?: {
    maxRetries?: number;
    backoff?: 'linear' | 'exponential';
    onRetry?: (attempt: number) => void;
  }
): Promise<T> {
  # YAGNI
}
```

---

### 验证 GREEN - 看它通过

- [ ] **强制执行。**
- [ ] 运行测试：`pytest path/to/test.test.ts`（或适当的命令）
- [ ] 确认测试通过
- [ ] 确认其他测试仍然通过
- [ ] 确认输出干净（没有错误、警告）

**测试失败？** 修复代码，而不是测试。

**其他测试失败？** 立即修复。

---

### REFACTOR - 清理

- [ ] 只在绿色之后
- [ ] 删除重复
- [ ] 改进名称
- [ ] 提取助手
- [ ] 保持测试绿色
- [ ] 不添加行为

---

## 🐛 Bug 修复 TDD

**Bug**：发现错误

### RED
```python
test('拒绝空电子邮件', async () => {
  const result = await submitForm({ email: '' });
  expect(result.error).toBe('Email required');
});
```

### 验证 RED
```bash
$ npm test
FAIL: expected 'Email required', got undefined
```

### GREEN
```python
def submitForm(data: FormData):
  if not data.email?.trim():
    return { error: 'Email required' }
  # ...
```

### 验证 GREEN
```bash
$ npm test
PASS
```

### REFACTOR
如果需要，为多个字段提取验证。

---

## 🚧 遇到困难时

| 问题 | 解决方案 |
|------|----------|
| 不知道如何测试 | 编写期望的 API。先编写断言。询问你的人类伙伴。 |
| 测试太复杂 | 设计太复杂。简化接口。 |
| 必须模拟所有内容 | 代码太耦合。使用依赖注入。 |
| 测试设置很大 | 提取助手。仍然复杂？简化设计。 |

---

## 📊 测试质量检查

| 质量 | 好 | 坏 |
|------|------|-----|
| **最小** | 一件事。名称中有"and"？拆分它。 | `test('验证电子邮件和域名和空格')` |
| **清晰** | 名称描述行为 | `test('test1')` |
| **显示意图** | 展示所需的 API | 掩盖代码应该做什么 |

---

## 🔗 集成调试

发现 Bug？编写失败测试来重现它。遵循 TDD 循环。测试证明修复并防止回归。

**永远不要在没有测试的情况下修复 bug。**

---

*记住：如果没有测试先失败，代码就不是 TDD。没有你的人类伙伴的许可，没有例外。* 🚀
