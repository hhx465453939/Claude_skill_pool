---
name: sam-dev-cc-init
description: PDCA循环开发工作流初始化工具。当用户输入 sam-init、pdca、init-pdca、pdca-init 或需要建立项目开发规范时使用。为AI辅助编程项目快速建立CLAUDE.md、PROGRESS-LOG.md、任务管理和经验沉淀机制。适合任何需要系统化开发流程的项目。
triggers:
  - sam-init
  - pdca
  - init-pdca
  - pdca-init
  - 初始化pdca
  - 建立开发规范
  - pdca workflow
---

# Sam Dev CC Init - PDCA 开发工作流

为任何新项目10秒内建立完整的AI辅助开发规范。

## 核心哲学

```
Context Window = RAM (易失，有限)
Filesystem = Disk (持久，无限)

→ 重要信息必须写入文件！
```

## 快速使用

```bash
# 在项目根目录执行
sam-init
# 或
pdca
```

## 触发条件

用户输入以下任一内容时激活：
- `sam-init`
- `pdca`
- `init-pdca`
- `pdca-init`
- `初始化pdca`
- `建立开发规范`
- `pdca workflow`

## 初始化操作指令

当触发时，按以下步骤执行：

### Step 1: 确认信息
1. 确认当前工作目录
2. 获取项目名称：从目录名或询问用户
3. 获取当前日期：`date +%Y-%m-%d`

### Step 2: 检查现有文件
检查以下文件是否已存在：
- `CLAUDE.md`
- `PROGRESS-LOG.md`
- `tasks/TASKS.md`
- `self.opt`

如果存在，提示用户并询问是否覆盖或跳过。

### Step 3: 读取模板
模板位置：`~/.config/agents/skills/sam-dev-cc-init/assets/`
- `CLAUDE.md.template`
- `PROGRESS-LOG.md.template`
- `TASKS.md.template`
- `self.opt.template`

### Step 4: 处理模板并创建文件
对每个模板执行：
1. 读取模板内容
2. 替换变量：
   - `{{PROJECT_NAME}}` → 实际项目名称
   - `{{DATE}}` → 当前日期（YYYY-MM-DD）
3. 写入目标位置（如果不存在）

目标文件结构：
```
project-root/
├── CLAUDE.md           # AI上下文指南（含PDCA流程、5问重启、最佳实践）
├── PROGRESS-LOG.md     # 进度日志（倒序追加）
├── self.opt            # 经验沉淀（错误模式、最佳实践）
└── tasks/
    └── TASKS.md        # 任务管理（当前Sprint、待办池、已完成）
```

### Step 5: 输出结果
显示创建的文件清单和使用提示，包括：
- 文件统计（创建/跳过）
- 文件说明
- 下一步建议
- 常用命令提示

---

## PDCA 开发循环

```
┌─────────────────────────────────────────────────────────────┐
│                    PDCA 开发循环                             │
├─────────────────────────────────────────────────────────────┤
│  1. PLAN  → 读取 tasks/TASKS.md，查看并领取任务              │
│  2. DO    → 开发实现 + 编写单元测试                          │
│  3. CHECK → pytest 验证 + 端到端API验证                      │
│  4. ACT   → 更新 PROGRESS-LOG.md（倒序追加）+ 更新任务状态   │
│  5. OPT   → 新错误模式写入 self.opt 经验沉淀                 │
└─────────────────────────────────────────────────────────────┘
```

### 文件对应关系

| 阶段 | 文件 | 用途 | 更新方式 |
|------|------|------|----------|
| PLAN | `tasks/TASKS.md` | 任务列表与状态管理 | 手动编辑 |
| DO | `src/` / `app/` / `tests/` | 代码实现 | 编码 |
| CHECK | `pytest` / `curl` | 验证测试 | 运行命令 |
| ACT | `PROGRESS-LOG.md` | 进度日志（**倒序追加**） | 手动编辑 |
| OPT | `self.opt` | 经验沉淀（错误模式、法则） | 手动编辑 |

---

## 日常使用工作流

### 会话恢复（重要！）

在长时间会话后、上下文重置后或新的一天开始时，运行：

```bash
# 运行会话恢复脚本
bash ~/.config/agents/skills/sam-dev-cc-init/scripts/session-catchup.sh
```

这会执行 **5-Question Reboot Test**：
| 问题 | 答案来源 |
|------|----------|
| Where am I? | 当前阶段在 `tasks/TASKS.md` |
| Where am I going? | 剩余任务列表 |
| What's the goal? | `tasks/TASKS.md` 中的项目目标 |
| What have I learned? | `self.opt` 中的经验沉淀 |
| What have I done? | `PROGRESS-LOG.md` 中的记录 |

### 每日启动

```bash
# 1. 查看今日任务
cat tasks/TASKS.md | grep -A 10 "当前 Sprint"

# 2. 回顾昨日进度
cat PROGRESS-LOG.md | head -40

# 3. 查看经验（避免重复踩坑）
cat self.opt | grep -A 3 "$(date +%Y-%m-%d)" || echo "继续积累..."

# 4. 检查PDCA完成状态
bash ~/.config/agents/skills/sam-dev-cc-init/scripts/check-complete.sh
```

### 开发循环（PDCA）

**PLAN**
1. 读取 `tasks/TASKS.md`
2. 选择优先级最高的 TODO 任务
3. 更新状态为 `IN_PROGRESS`

**DO**
1. 实现代码（遵循2-Action Rule）
2. 编写/运行单元测试
3. 遇到错误 → 记录到 `self.opt`

**CHECK**
1. 运行 `pytest` 验证
2. 端到端验证（如 API 测试）
3. 代码质量检查（可选）

**ACT**
1. 在 `PROGRESS-LOG.md` **顶部（倒序）**追加今日完成
2. 更新 `tasks/TASKS.md` 任务状态为 `DONE`
3. 填写实际耗时

**OPT（Agent 自优化）**
<!-- OPT = Agent Self-Optimization，不是简单记录错误，而是 AI 进化 -->

4. **判断：这个偏差值不值得永久记录？**
   - ❌ 一般性错误（语法、拼写）→ 不记录（AI 自己能避免）
   - ⚠️ 一次性领域错误 → 记录在 PROGRESS-LOG.md 即可
   - ✅ 关键偏差（>3次尝试/反直觉/会再犯）→ 记录到 `self.opt`

5. **提取关键偏差模式（CDP）**
   - 偏差描述：AI 最初的错误判断是什么
   - 根因：认知盲区？过度泛化？上下文缺失？
   - 解决策略：核心思路（一句话）
   - 预防触发器：什么信号出现时要警惕

6. **提炼核心解决策略（CRS）**
   - 策略是否跨项目可复用？
   - 是否是「方法论」而非「具体命令」？
   - 记录到「核心解决策略库」

**→ 返回 PLAN，领取下一个任务（带着进化后的认知）**

### 任务完成 Checklist

- [ ] 代码实现完成
- [ ] 单元测试通过 (`pytest`)
- [ ] 集成测试通过（如有）
- [ ] `PROGRESS-LOG.md` 已更新（**倒序追加**）
- [ ] `tasks/TASKS.md` 状态已更新为 `DONE`
- [ ] Agent 自优化：关键偏差已提取到 `self.opt`（如适用）

---

## 关键规则

### 1. 倒序追加原则
`PROGRESS-LOG.md` 永远在最上面写新内容，旧内容自动下沉。

### 2. 2-Action Rule
> 每进行2个 view/browser/search 操作后，**立即**将关键发现写入文本文件。

### 3. Read Before Decide
做重大决策前，重新阅读 `tasks/TASKS.md` 和 `PROGRESS-LOG.md`。

### 4. Agent 自优化原则（不是记所有错误）
<!-- 
  不是流水账式记录，而是提取「关键偏差」→「核心解决策略」
  一般性错误 AI 自己能避免，不需要记录
-->
只记录：
- 花了 >3 次尝试才解决的（说明初始直觉错误）
- 解决策略是「反直觉」或「跨领域迁移」的
- 类似场景下「大概率会再犯」的
- 导致显著时间浪费（>20分钟）的认知偏差

### 5. Never Repeat Failures
```
if action_failed:
    next_action != same_action
```

---

## 3-Strike Error Protocol

```
ATTEMPT 1: 诊断与修复
  → 仔细阅读错误
  → 识别根本原因
  → 应用针对性修复

ATTEMPT 2: 替代方法
  → 同样错误？尝试不同方法
  → 换工具？换库？
  → 绝不重复相同的失败操作

ATTEMPT 3: 重新思考
  → 质疑假设
  → 搜索解决方案
  → 考虑更新计划

AFTER 3 FAILURES: 升级给用户
  → 解释尝试过的方法
  → 分享具体错误
  → 请求指导
```

---

## 辅助脚本

本 skill 包含以下辅助脚本：

| 脚本 | 用途 | 使用方法 |
|------|------|----------|
| `scripts/init.sh` | 初始化所有PDCA文件 | `bash ~/.config/agents/skills/sam-dev-cc-init/scripts/init.sh [项目名]` |
| `scripts/check-complete.sh` | 检查今日PDCA完成状态 | `bash ~/.config/agents/skills/sam-dev-cc-init/scripts/check-complete.sh` |
| `scripts/session-catchup.sh` | 恢复会话上下文 | `bash ~/.config/agents/skills/sam-dev-cc-init/scripts/session-catchup.sh` |

---

## 模板内容参考

### CLAUDE.md 包含
- 快速开始与常用命令
- PDCA循环流程图
- 文件对应关系表
- 5-Question Reboot Test
- 开发循环详细流程
- 关键规则（倒序追加、2-Action Rule等）
- 3-Strike Error Protocol
- Read vs Write 决策矩阵

### PROGRESS-LOG.md 包含
- 用途说明（倒序追加）
- 记录规范
- 错误记录格式
- 测试记录格式
- 初始条目：项目初始化

### tasks/TASKS.md 包含
- 项目目标
- 当前 Sprint 表格
- 待办池
- 已完成归档
- 关键决策表
- 错误日志
- 风险与阻塞

### self.opt 包含（Agent 自优化日志）
- **项目信息** + 快速命令备忘
- **关键偏差模式（CDP）**：偏差→根因→解决策略→预防触发器
- **核心解决策略库（CRS）**：可复用的方法论级策略
- **认知盲区档案（CBS）**：AI 容易「看不见」的场景
- **效率法则（Laws）**：经过验证的效率提升法则
- **假设验证记录**：做过的假设及其验证结果
- **记录决策树**：帮助 AI 判断「什么值得记录」

---

## 更新机制

当本 skill 更新后：
1. 已有项目不受影响（保持独立）
2. 新项目自动使用最新模板
3. 如需同步更新旧项目：手动复制模板内容

---

## 最佳实践提示

1. **倒序追加**：PROGRESS-LOG.md 永远在最上面写新内容
2. **原子提交**：一个任务一个 commit，便于回滚
3. **及时记录**：踩坑后立即写 self.opt，不要等
4. **简洁原则**：日志只写要点，不写流水账
5. **AI友好**：CLAUDE.md 是给AI看的，写清楚上下文
6. **定期恢复**：使用 session-catchup.sh 恢复上下文
7. **检查完成**：使用 check-complete.sh 验证PDCA循环
