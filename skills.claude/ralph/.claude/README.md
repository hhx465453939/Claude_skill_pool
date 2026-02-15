# Ralph Slash Commands for Claude Code

可移植的 Ralph 自主 Agent 循环系统配置。

Ralph 是一个自主 AI Agent 循环系统，提供 **两种执行模式** 完成项目开发：
1. **Classic Ralph** - 通过重复运行 Amp 来完成 PRD（需要 Amp CLI）
2. **Ralph YOLO** - 直接使用 Claude Code 子 Agent 完成（无需 Amp！）✨

内存通过 git 历史、`prd-progress.txt` 和 `prd.json` 持久化。

## 目录

- [两种执行模式对比](#两种执行模式对比)
- [安装](#安装)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [重要配置](#重要配置)
- [使用方法](#使用方法)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

---

## 两种执行模式对比

### Classic Ralph (原版)

**优点：**
- 成熟稳定，经过验证
- 完全独立的 Amp 实例
- 适合大规模项目

**缺点：**
- ❌ 需要 Amp CLI
- ❌ 需要 jq 工具
- ❌ 需要配置 bash 脚本
- ❌ 外部循环管理

**使用场景：**
- 已有 Amp 环境的专业用户
- 需要完全隔离的开发环境

### Ralph YOLO (新版推荐！)

**优点：**
- ✅ 无需 Amp CLI！只用 Claude Code
- ✅ 无需 jq 和其他依赖
- ✅ 主会话保持完整上下文
- ✅ 实时进度跟踪和监控
- ✅ 可以随时中断和恢复
- ✅ 更容易调试和干预

**缺点：**
- 新功能，可能存在未知问题

**使用场景：**
- 快速原型开发
- 不想安装 Amp 的用户
- 需要实时监控开发进度
- 免费版 Claude Code 用户（无 Amp）ノ(✿ﾟ▽ﾟ)ノ

**推荐：** 大多数用户应该优先尝试 **Ralph YOLO**！

## 安装

将此 `.claude/` 目录复制到你的项目根目录：

```bash
# 方法 1: 直接复制
cp -r /path/to/ralph/.claude /your/project/.claude

# 方法 2: 使用符号链接（开发 Ralph 时）
ln -s /path/to/ralph/.claude /your/project/.claude
```

验证安装：

```bash
# 检查目录结构
ls -la .claude/

# 检查脚本权限
## 赋权可执行
chmod +x .claude/scripts/ralph.sh
# 查看当前权限
ls -la .claude/scripts/ralph.sh

# 应该显示类似这样的输出：
# -rwxr-xr-x 1 user group 5119 Jan 16 13:49 ralph.sh
#  ^^ ^^^ ^^^
#  || | || |
#  || | || +-- 其人权限 (read/execute)
#  || | +----- 组权限 (read/execute)
#  || +------- 所有者权限 (read/write/execute)
#  |+--------- 普通文件
#  +---------- 可执行？

# 移除可执行权限
chmod -x .claude/scripts/ralph.sh

# 给所有用户添加可执行权限
chmod a+x .claude/scripts/ralph.sh
# a = all（所有用户）

常用的数字方式 (๑•̀ㅂ•́)✧：

# 755 = rwxr-xr-x（所有者可读写执行，其他人可读执行）
chmod 755 .claude/scripts/ralph.sh

# 744 = rwxr--r--（所有者可读写执行，其他人只读）
chmod 744 .claude/scripts/ralph.sh```

## 前置要求

### 1. Amp CLI

[Amp CLI](https://ampcode.com) 必须已安装并认证：

```bash
# 检查安装
which amp
amp --version

# 如果未安装，访问 https://ampcode.com 安装
```

### 2. jq 工具

`jq` 是处理 JSON 的命令行工具：

```bash
# 检查安装
which jq

# macOS
brew install jq

# Linux/Ubuntu
sudo apt-get install jq

# Linux/CentOS
sudo yum install jq
```

### 3. Git 仓库

确保你的项目是一个 Git 仓库：

```bash
# 初始化仓库（如果还没有）
git init

# 检查状态
git status
```

## 快速开始

### (推荐)直接一次性完成对话
#### 新开一个对话

/PRD 请遍历项目后生成可用于/ralph 的 PRD 文件，用于实现以下目标：XXXX；，并启动 /ralph，在XXX个循环内完成开发任务。 

### 步骤 1: 生成 PRD

使用 Claude Code 的 `/prd` 命令：

```
/prd "添加用户认证功能"
```

PRD skill 会：
- 询问 3-5 个澄清问题（带选项）
- 生成结构化的 PRD 文档
- 保存到 `tasks/prd-[feature-name].md`

### 步骤 2: 运行 Ralph

使用 `/ralph` 命令：

```
/ralph tasks/prd-user-auth.md
```

Ralph skill 会：
- 将 PRD 转换为 `prd.json`
- 创建功能分支
- 启动自主循环实现每个用户故事

### 步骤 3: 监控进度

```bash
# 查看已完成的用户故事
cat prd.json | jq '.userStories[] | {id, title, passes}'

# 查看进度日志
cat prd-progress.txt

# 查看 git 提交历史
git log --oneline -10
```

## 重要配置

### ⚠️ 脚本执行权限（必须）

ralph.sh 脚本必须有可执行权限：

```bash
# 检查权限
ls -la .claude/scripts/ralph.sh

# 如果没有执行权限，添加权限
chmod +x .claude/scripts/ralph.sh

# 验证（应该显示 -rwxr-xr-x）
ls -la .claude/scripts/ralph.sh
```

**如果脚本没有执行权限，Ralph 将无法运行！**

### 🔄 Amp 自动切换（推荐）

当任务超过单个上下文窗口时，启用 Amp 的自动切换功能：

编辑 `~/.config/amp/settings.json`：

```json
{
  "amp.experimental.autoHandoff": { "context": 90 }
}
```

**这会让 Ralph 在上下文使用率达到 90% 时自动切换到新实例**，实现：
- 处理更大的任务
- 避免上下文溢出
- 自动保持上下文连贯性

如果没有启用此功能，大型任务可能会：
- 上下文填满后失败
- 生成不完整的代码
- 迭代效率降低

### 🔁 循环次数配置

默认最大迭代次数是 **10 次**。

修改循环次数：

```bash
# 方法 1: 命令行参数（推荐）
bash .claude/scripts/ralph.sh 20

# 方法 2: 编辑配置文件
# 编辑 .claude/ralph-config.json
{
  "ralph": {
    "maxIterations": 20
  }
}
```

**如何选择循环次数：**
- 小型功能（3-5 个故事）：10 次
- 中型功能（6-15 个故事）：20 次
- 大型功能（16+ 个故事）：30-50 次

**注意：** 如果循环次数用完但任务未完成，Ralph 会保存状态并退出。你可以直接再次运行，它会从停止处继续。

### 📁 其他配置选项

编辑 `.claude/ralph-config.json`：

```json
{
  "prd": {
    "outputDir": "tasks",              // PRD 输出目录
    "filenamePattern": "prd-{slug}.md" // PRD 文件名模式
  },
  "ralph": {
    "maxIterations": 10,               // 最大迭代次数
    "branchPrefix": "ralph/",          // 分支前缀
    "archiveDir": ".claude/archive",   // 归档目录
    "progressFile": "prd-progress.txt",// 进度文件名
    "prdFile": "prd.json"              // PRD 文件名
  },
  "amp": {
    "autoHandoffContext": 90           // 自动切换阈值（百分比）
  }
}
```

## 使用方法

### `/prd` - 生成 PRD

```
/prd "功能描述"
```

**示例：**

```
/prd "添加任务优先级功能"
```

PRD skill 会询问澄清问题，你可以用选项快速回答：

```
1. 主要目标是什么？
   A. 改善用户体验
   B. 提高用户留存率
   C. 减少支持工作量

你的回答：1A
```

### `/ralph` - 运行 Ralph

```
/ralph [路径]
```

**用法：**

```bash
# 从 PRD 创建并运行
/ralph tasks/prd-my-feature.md

# 从现有 prd.json 运行
/ralph prd.json

# 直接运行（查找 prd.json）
/ralph
```

### 直接运行脚本

你也可以直接运行脚本，不通过 Claude Code：

```bash
# 使用默认循环次数（10次）
bash .claude/scripts/ralph.sh

# 指定循环次数
bash .claude/scripts/ralph.sh 20
```

### 监控命令

```bash
# 查看用户故事完成状态
cat prd.json | jq '.userStories[] | {id, title, passes}'

# 只看未完成的故事
cat prd.json | jq '.userStories[] | select(.passes == false) | {id, title, priority}'

# 查看进度日志
cat prd-progress.txt

# 查看 git 提交历史
git log --oneline -10

# 查看当前分支
git branch --show-current
```

## 故障排除

### 问题 1: 脚本没有执行权限

**症状：**
```
bash: .claude/scripts/ralph.sh: Permission denied
```

**解决：**
```bash
chmod +x .claude/scripts/ralph.sh
```

### 问题 2: Amp CLI 未安装

**症状：**
```
amp: command not found
```

**解决：**
访问 https://ampcode.com 安装 Amp CLI。

### 问题 3: jq 未安装

**症状：**
```
jq: command not found
```

**解决：**
```bash
# macOS
brew install jq

# Linux/Ubuntu
sudo apt-get install jq
```

### 问题 4: Git 工作区不干净

**症状：**
Ralph 拒绝启动，提示有未提交的更改。

**解决：**
```bash
# 提交更改
git add .
git commit -m "WIP"

# 或暂存更改
git stash

# 或清理更改
git checkout .
```

### 问题 5: prd.json 不存在

**症状：**
```
Error: prd.json not found
```

**解决：**
```
/ralph tasks/prd-your-feature.md
```

先指定 PRD 文件让 Ralph 生成 prd.json。

### 问题 6: Amp 上下文填满

**症状：**
- Amp 运行缓慢
- 生成不完整的代码
- 迭代失败

**解决：**
1. 启用自动切换（见上文配置）
2. 拆分大型用户故事
3. 减少每个故事的代码量

### 问题 7: Ralph 中途停止

**症状：**
Ralph 在某个迭代后停止，但任务未完成。

**解决：**
```bash
# 直接再次运行，会从停止处继续
bash .claude/scripts/ralph.sh

# 查看最后完成的故事
cat prd-progress.txt | tail -20

# 检查是否有失败的提交
git log --oneline -5
```

### 问题 8: 故事质量检查失败

**症状：**
Ralph 停止运行，但有未提交的代码。

**解决：**
```bash
# 查看错误
cat prd-progress.txt | tail -20

# 检查代码
git status
git diff

# 手动修复后重新运行
bash .claude/scripts/ralph.sh
```

## 最佳实践

### 1. 用户故事大小

**每个故事必须在一个迭代内完成。**

✅ **正确大小：**
- 添加数据库列和迁移
- 向现有页面添加 UI 组件
- 更新服务器操作
- 添加过滤下拉菜单

❌ **太大（必须拆分）：**
- "构建整个仪表板"
- "添加认证"
- "重构 API"

**经验法则：** 如果不能用 2-3 句话描述变更，就太大了。

### 2. 依赖顺序

故事按 `priority` 顺序执行。前面的故事不能依赖后面的。

✅ **正确顺序：**
1. Schema/数据库变更
2. 服务器操作 / 后端逻辑
3. UI 组件
4. 聚合视图

❌ **错误顺序：**
1. UI 组件（依赖 schema）
2. Schema 变更

### 3. 验收标准

每个标准必须可验证。

✅ **好的标准：**
- "Add status column to tasks table with default 'pending'"
- "Typecheck passes"
- "Tests pass"

❌ **差的标准：**
- "Works correctly"
- "Good UX"

### 4. 干净的 Git 状态

始终从干净的 git 状态开始 Ralph：

```bash
# 检查状态
git status

# 清理或提交
git add .
git commit -m "Before Ralph run"
```

### 5. 监控进度

定期检查：

```bash
# 每几次迭代后检查
cat prd-progress.txt
git log --oneline -5
```

### 6. 读取学习内容

每次迭代都会在 `prd-progress.txt` 中记录学习内容。新迭代开始前先读取它！

## 项目结构

```
.claude/
├── skills/              # Claude Code skills
│   ├── prd.md          # PRD 生成技能
│   └── ralph.md        # Ralph 执行技能
├── scripts/            # Ralph 执行脚本
│   ├── ralph.sh        # 主循环脚本（必须有执行权限！）
│   └── prompt.md       # Amp 实例指令模板
├── templates/          # 模板文件
│   └── prd.json.example
├── archive/            # 历史运行归档（自动生成）
├── ralph-config.json   # 配置文件
└── README.md           # 本文档
```

## 生成的文件

Ralph 运行时会在项目根目录生成：

```
your-project/
├── prd.json            # 用户故事和状态
├── prd-progress.txt    # 进度日志
├── tasks/              # PRD 文档目录
│   └── prd-*.md
└── .claude/
    ├── .last-branch    # 上次运行的分支
    └── archive/        # 归档的旧运行记录
        └── YYYY-MM-DD-feature-name/
            ├── prd.json
            └── prd-progress.txt
```

## 示例会话

```
User: /prd "添加任务优先级功能"

PRD Skill:
1. 主要目标是什么？
   A. 改善用户引导体验
   B. 提高用户留存率
   C. 减少支持工作量
   D. 其他: [请说明]

User: 1D, 让用户专注于重要任务

PRD Skill:
2. 目标用户是谁？
   A. 新用户
   B. 现有用户
   C. 管理员
   D. 所有用户

User: 2D

PRD Skill:
[继续询问...]

PRD Skill:
✓ PRD 已生成并保存到 tasks/prd-task-priority.md
包含 4 个用户故事：
- US-001: Add priority field to database
- US-002: Display priority indicator
- US-003: Add priority selector
- US-004: Filter by priority

User: /ralph tasks/prd-task-priority.md

Ralph Skill:
✓ 正在转换 PRD 到 prd.json...
✓ 已创建包含 4 个用户故事的 prd.json
✓ 检查前置条件...
✓ 创建分支 ralph/task-priority...
✓ 启动 Ralph 循环...

[Ralph 执行迭代...]

Iteration 1: US-001 - Add priority field to database ✓
Iteration 2: US-002 - Display priority indicator on task cards ✓
Iteration 3: US-003 - Add priority selector to task edit ✓
Iteration 4: US-004 - Filter tasks by priority ✓

<promise>COMPLETE</promise>

✓ 所有故事已完成！
查看详情: cat prd-progress.txt
查看提交: git log --oneline
```

## 原理

Ralph 基于 [Geoffrey Huntley 的 Ralph 模式](https://ghuntley.com/ralph/)。

**核心思想：**
- 每个 AI 实例都有有限的上下文
- 大型任务需要分解为小故事
- 每次迭代都是全新的开始
- 通过 git 和文件持久化状态

**迭代间的内存：**

每次迭代都是**全新的 Amp 实例**，没有之前工作的记忆。

唯一的跨迭代状态：
- Git 历史（之前迭代的提交）
- `prd-progress.txt`（学习内容和上下文）
- `prd.json`（哪些故事已完成）

## 许可证

与原 Ralph 项目相同。

## 更多信息

- [Ralph 原始项目](https://github.com/snarktank/ralph)
- [Amp 文档](https://ampcode.com/manual)
- [Geoffrey Huntley 的 Ralph 文章](https://ghuntley.com/ralph/)
- [作者的 Twitter 帖子](https://x.com/ryancarson/status/2008548371712135632)
