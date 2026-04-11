# Superpowers 快速参考指南 🚀

## 一句话总结

**Superpowers 是一个基于 TDD 和系统化开发的 AI 编码代理框架，让你的 AI 代理具备真正的工程能力。**

---

## 核心工作流

```
需求 → Brainstorming → 设计规范 → 编写计划 → TDD 实现 → 代码审查 → 完成
```

---

## 何时使用哪个技能

| 场景 | 使用技能 | 说明 |
|------|---------|------|
| 创建新功能 | `brainstorming` | 先设计，再实现 |
| 编写实现计划 | `writing-plans` | 细粒度任务（2-5 分钟） |
| 编写代码 | `test-driven-development` | 测试优先！ |
| 代码审查 | `requesting-code-review` | 任务之间自动触发 |
| 并行开发 | `using-git-worktrees` | 隔离的工作空间 |
| 执行计划（有子代理） | `subagent-driven-development` | 推荐！ |
| 执行计划（无子代理） | `executing-plans` | 批量执行 |
| 调试问题 | `systematic-debugging` | 系统性方法 |
| 完成分支 | `finishing-a-development-branch` | 清理和合并 |

---

## TDD 铁律

```
没有失败的测试，就没有生产代码
```

**违反规则的字面意思就是违反规则的精神。**

---

## RED-GREEN-REFACTOR 循环

```
RED → 编写失败的测试
  ↓
验证 RED → 看它失败（强制执行）
  ↓
GREEN → 编写最小代码
  ↓
验证 GREEN → 看它通过（强制执行）
  ↓
REFACTOR → 清理（仅当绿色时）
  ↓
下一个失败测试
```

---

## 快速检查清单

### 开始任何实现之前 ✅

- [ ] 是否有设计规范？
- [ ] 是否有实现计划？
- [ ] 是否有测试用例？
- [ ] 是否遵循了 TDD？

### 完成任何任务之后 ✅

- [ ] 测试通过了吗？
- [ ] 输出干净吗（没有警告）？
- [ ] 是否提交了？
- [ ] 代码审查通过了吗？

---

## 常见错误

### ❌ 不要这样做

- 在没有设计的情况下实现功能
- 在测试之前编写代码
- 跳过 TDD（即使是"简单"项目）
- 编写大而复杂的任务
- 跳过代码审查

### ✅ 应该这样做

- 每个项目都通过设计流程
- 测试优先！
- 细粒度任务（2-5 分钟）
- 频繁提交
- 系统性方法而非临时性

---

## 关键原则

1. **TDD** - 测试驱动开发，没有测试的代码都是假的
2. **DRY** - Don't Repeat Yourself，避免重复
3. **YAGNI** - You Aren't Gonna Need It，不要添加不必要的功能
4. **系统性方法** - 告别临时性的代码
5. **复杂性降低** - 简单是首要目标
6. **证据优于声明** - 验证后再说成功

---

## 文件位置

### 输出文件

```
docs/superpowers/
├── specs/                      # 设计规范
│   └── YYYY-MM-DD-<topic>-design.md
└── plans/                      # 实现计划
    └── YYYY-MM-DD-<feature-name>.md
```

### 技能目录

```
skills/superpowers/
├── SKILL.md                    # 主技能文件
├── scripts/                    # 脚本和工具
│   └── tdd-checklist.md        # TDD 检查清单
├── references/                 # 参考资料
│   └── quick-start.md         # 快速参考（本文件）
├── templates/                  # 文档模板
│   ├── design-spec-template.md
│   └── implementation-plan-template.md
├── tasks/                      # 任务模板
└── archive/                    # 归档文件
```

---

## 与其他技能的配合

### 与 Ralph 配合

- **Ralph**：从 PRD 到代码实现的完整流程
- **Superpowers**：严格的工程方法论

**流程**：
1. Ralph 生成 PRD
2. Superpowers Brainstorming 细化设计
3. Superpowers Writing Plans 创建详细计划
4. Superpowers TDD 实现功能
5. Superpowers Code Review 保证质量

### 与 Code-Debugger 配合

- **Code-Debugger**：代码调试和增量开发
- **Superpowers**：系统性调试方法论

**流程**：
1. Superpowers Systematic Debugging 定位根因
2. Code-Debugger 深度上下文分析修复
3. Superpowers TDD 编写测试防止回归

---

## 示例对话

### 用户："帮我创建一个用户认证功能"

**AI（使用 Superpowers）**：
1. 触发 `brainstorming` 技能
2. 询问澄清问题（一次一个）
3. 提出方案并讨论权衡
4. 展示设计并获取批准
5. 编写设计规范到 `docs/superpowers/specs/YYYY-MM-DD-auth-design.md`
6. 触发 `writing-plans` 技能
7. 创建详细实现计划到 `docs/superpowers/plans/YYYY-MM-DD-auth-implementation.md`
8. 触发 `test-driven-development` 技能
9. 遵循 RED-GREEN-REFACTOR 循环实现功能
10. 触发 `requesting-code-review` 技能
11. 完成并合并分支

---

## 获取帮助

### 遇到困难？

1. 查看 `scripts/tdd-checklist.md` - TDD 检查清单
2. 查看 `templates/` - 文档模板
3. 查看主 `SKILL.md` - 完整文档

### 常见问题

**Q: 这个项目太简单了，不需要设计吧？**
A: 不需要。每个项目都经历这个过程。"简单"的项目是未检查的假设造成最多浪费的地方。

**Q: 我会在实现之后编写测试，这样更快吧？**
A: 不需要。立即通过的测试证明不了任何东西。测试优先强制你看到测试失败，证明它实际上测试了某些东西。

**Q: 但是我已经手动测试了所有边缘情况！**
A: 临时 ≠ 系统性。没有记录，无法重新运行。自动化测试每次都以相同的方式运行。

**Q: TDD 会让我变慢吗？**
A: 不会。TDD 比调试更快。"实用" = 测试优先。

---

## 记住

**让每个 AI 代理都具备真正的工程能力！** 🚀✨

---

*使用 Superpowers 框架生成*
