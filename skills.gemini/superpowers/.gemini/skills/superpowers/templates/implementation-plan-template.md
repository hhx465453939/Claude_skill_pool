# [功能名称] 实现计划

> **对于代理工作者**：**必需**：使用 superpowers:subagent-driven-development（如果子代理可用）或 superpowers:executing-plans 来实现此计划。步骤使用复选框（`- [ ]`）语法进行跟踪。

**目标**：[一句话描述这个功能构建什么]

**架构**：[2-3 句话关于方法]

**技术栈**：[关键技术/库]

**创建日期**：YYYY-MM-DD
**状态**：Draft / In Progress / Completed

---

## 文件结构

```
[项目根目录]
├── [新文件 1]
├── [新文件 2]
├── [修改的文件 1]
└── [修改的文件 2]
```

### 文件职责

| 文件 | 职责 |
|------|------|
| [文件 1] | [它做什么] |
| [文件 2] | [它做什么] |

---

## 任务列表

---

### Chunk 1: [第一阶段名称]

---

#### Task 1: [组件名称 1]

**文件**：
- 创建：`exact/path/to/file1.py`
- 修改：`exact/path/to/existing.py:123-145`
- 测试：`tests/exact/path/to/test1.py`

- [ ] **Step 1: 编写失败的测试**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: 运行测试以验证它失败**

运行：`pytest tests/path/test.py::test_name -v`
预期：FAIL with "function not defined"

- [ ] **Step 3: 编写最小实现**

```python
def function(input):
    return expected
```

- [ ] **Step 4: 运行测试以验证它通过**

运行：`pytest tests/path/test.py::test_name -v`
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```

---

#### Task 2: [组件名称 2]

**文件**：
- 创建：`exact/path/to/file2.py`
- 修改：`exact/path/to/existing.py:200-220`
- 测试：`tests/exact/path/to/test2.py`

- [ ] **Step 1: 编写失败的测试**

```python
def test_another_behavior():
    # 测试代码
    pass
```

- [ ] **Step 2: 运行测试以验证它失败**

运行：`pytest tests/path/test2.py::test_name -v`
预期：FAIL

- [ ] **Step 3: 编写最小实现**

```python
def another_function(input):
    # 实现代码
    pass
```

- [ ] **Step 4: 运行测试以验证它通过**

运行：`pytest tests/path/test2.py::test_name -v`
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add tests/path/test2.py src/path/file2.py
git commit -m "feat: add another feature"
```

---

### Chunk 2: [第二阶段名称]

---

#### Task 3: [组件名称 3]

**文件**：
- 创建：`exact/path/to/file3.py`
- 修改：`exact/path/to/existing.py:300-350`
- 测试：`tests/exact/path/to/test3.py`

- [ ] **Step 1: 编写失败的测试**

```python
def test_third_behavior():
    # 测试代码
    pass
```

- [ ] **Step 2: 运行测试以验证它失败**

运行：`pytest tests/path/test3.py::test_name -v`
预期：FAIL

- [ ] **Step 3: 编写最小实现**

```python
def third_function(input):
    # 实现代码
    pass
```

- [ ] **Step 4: 运行测试以验证它通过**

运行：`pytest tests/path/test3.py::test_name -v`
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add tests/path/test3.py src/path/file3.py
git commit -m "feat: add third feature"
```

---

## 验证清单

### 每个任务后

- [ ] 所有测试通过
- [ ] 输出干净（没有错误、警告）
- [ ] 代码遵循 DRY、YAGNI 原则
- [ ] 测试使用真实代码（仅在不可避免时使用 mocks）
- [ ] 提交消息清晰描述变更

### 完整计划后

- [ ] 所有任务完成
- [ ] 所有测试通过（包括回归测试）
- [ ] 代码审查通过
- [ ] 文档更新（如果需要）
- [ ] 功能符合设计规范

---

## 常见问题排查

### 问题：测试在 Step 2 没有失败

**解决方案**：
- 检查测试是否测试了现有行为
- 修改测试以测试新功能
- 重新运行直到正确失败

### 问题：测试在 Step 4 没有通过

**解决方案**：
- 检查实现是否正确
- 不要修改测试
- 编写最简单的代码来通过测试

### 问题：其他测试开始失败

**解决方案**：
- 立即修复
- 检查是否破坏了现有功能
- 考虑是否需要重构

---

## 注意事项

⚠️ **重要**：
- 确切的文件路径总是必需的
- 计划中的完整代码（不是"添加验证"）
- 确切的命令和预期输出
- 使用 @ 语法引用相关技能
- DRY、YAGNI、TDD、频繁提交

---

*使用 Superpowers 框架生成*
