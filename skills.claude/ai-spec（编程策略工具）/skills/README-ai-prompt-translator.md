# AI 指令优化 Skill 使用指南

## 概述

这个 skill 的核心功能是将用户模糊的自然语言需求转换为精确的、生产级的技术规范和 AI 可执行指令。

## 两种调用方式

### 方式 1: 使用 Slash Command（推荐）

```bash
/ai-spec
```

然后输入你的需求描述。

**示例**:
```bash
/ai-spec

我需要创建一个 Web API，用于管理待办事项列表。
需要支持用户注册、登录、创建、编辑、删除和查询待办事项。
要求响应时间小于 100ms，支持至少 1000 并发用户。
```

### 方式 2: 直接使用 Skill

在对话中直接调用：

```
请使用 ai-prompt-translator skill 分析以下需求...
```

## 工作流程

当调用这个 skill 后，它会执行以下步骤：

### 1️⃣ 需求审计（Requirement Audit）
- 识别核心功能需求
- 挖掘隐含的非功能性需求（性能、并发、安全、可维护性）
- 标注缺失的关键信息

### 2️⃣ 最优架构搜索（Best-of-N Architecture Search）
- 对比 2-3 种技术实现路径
- 根据性能、开发效率、生态成熟度选择最佳方案
- 给出清晰的选型理由

### 3️⃣ 技术规格生成（Spec Generation）
生成详细的技术规格书，包含：
- 架构决策记录（ADR）
- 系统设计（目录结构、数据模型、关键流程）
- 详细实现要求（错误处理、测试、安全、性能）

### 4️⃣ 生成"神级"指令（God Prompt）
生成一段极尽详细的 Prompt，可以直接投喂给：
- **Claude Code**
- **Cursor Composer**
- **Windsurf**
- 其他 AI 编程工具

## 输出格式示例

```markdown
# Todo List API: 技术规范与 AI 指令

## 1. 需求审计总结
- **核心需求**: 待办事项管理的 CRUD API + 用户认证
- **隐含需求**:
  - 数据持久化（数据库）
  - 用户会话管理（JWT/Session）
  - API 限流（防止滥用）
  - 数据验证（防止注入攻击）
- **缺失信息**: 部署环境（云服务/本地）、前端框架需求

## 2. 架构决策记录 (ADR)
- **Selected Stack**: Node.js + TypeScript + NestJS + PostgreSQL + Redis
- **Rationale**: ...
- **Design Pattern**: Clean Architecture + Repository Pattern
- **Trade-offs**: ...

## 3. 系统设计
### 3.1 目录结构
```bash
/todo-api
  /src
    /domain      # 实体、值对象
    /application # 用例、业务逻辑
    /infrastructure # 数据库、外部服务
    /interfaces  # REST controllers
  /tests
```

### 3.2 核心数据模型
```typescript
interface Todo {
  id: string;
  userId: string;
  title: string;
  description?: string;
  status: 'pending' | 'completed';
  dueDate?: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

### 3.3 关键逻辑流程
- **Auth Flow**: JWT Token 验证流程
- **Todo CRUD**: 创建、更新、删除的事务处理

## 4. 详细实现要求
- **Error Handling**: 统一错误中间件，HTTP 状态码映射
- **Testing**: Jest 单元测试 + Supertest 集成测试，覆盖率 > 80%
- **Security**: class-validator 输入验证、Helmet.js 安全头、Rate Limiting
- **Performance**: Redis 缓存用户会话，数据库连接池，索引优化

## 5. 给 AI 编程工具的执行指令

[完整的、可直接执行的指令文档]
```

## 使用场景

### ✅ 适合使用的场景

1. **新项目开发**: 从零开始一个完整项目
2. **功能模块设计**: 设计复杂的功能模块（如支付系统、消息队列）
3. **技术选型决策**: 需要客观的技术栈对比和选择
4. **重构规划**: 现有代码的重构方案设计
5. **性能优化**: 系统性能优化方案

### ❌ 不适合使用的场景

1. **简单的代码修改**: 如"修复这个 bug"或"重命名这个函数"
2. **代码解释**: "这段代码是做什么的？"
3. **简单的查询**: "如何使用 Python 的列表推导式？"
4. **特定文件的操作**: 如"运行测试"、"提交代码"

## 高级功能：多线程 Sub-Agent 开发

对于复杂项目，skill 生成的指令可以自动触发多个并行的 sub-agent：

```markdown
## 并行开发计划

### Agent 1: 基础设施层
- 数据库模型和迁移
- Redis 配置
- 环境变量管理

### Agent 2: 业务逻辑层
- 用户认证服务
- Todo CRUD 服务
- 输入验证和错误处理

### Agent 3: 接口层
- REST API 控制器
- Swagger 文档生成
- 请求/响应 DTO

### Agent 4: 测试和文档
- 单元测试
- 集成测试
- README 和 API 文档
```

## 最佳实践

### 1. 提供清晰的需求描述

**好的示例**:
```
我需要创建一个实时聊天应用，支持：
- 私聊和群聊
- 消息持久化
- 在线状态显示
- 文件分享（图片、文档）
- 端到端加密（可选）

技术要求：
- 支持至少 10,000 并发连接
- 消息延迟 < 100ms
- 可水平扩展
```

**不好的示例**:
```
做一个聊天应用
```

### 2. 明确非功能性需求

如果对性能、安全、可扩展性有要求，请明确说明：
- 并发用户数
- 响应时间要求
- 数据规模
- 安全级别（是否需要加密、审计日志等）
- 部署环境（云服务、本地服务器、边缘计算等）

### 3. 指定约束条件

如果有限制条件，请说明：
- 团队熟悉的技术栈
- 现有系统需要集成
- 预算限制
- 时间限制

## 工作流程示例

```bash
# 步骤 1: 调用 skill
/ai-spec

# 步骤 2: 输入需求
我需要创建一个电商平台的订单系统...

# 步骤 3: AI 生成技术规范和执行指令
[输出完整的技术文档]

# 步骤 4: 复制 AI 执行指令，让 Claude Code 自动执行
[Claude Code 开始创建项目、编写代码、运行测试]
```

## 故障排除

### 问题：生成的技术栈不符合预期

**解决方案**: 在需求中明确指定技术栈偏好，或询问 AI 为何选择某个技术栈，可以进行二次调整。

### 问题：指令过于复杂，无法一次性执行

**解决方案**: 将生成的指令分阶段执行，或使用生成的"并行开发计划"启动多个 sub-agent。

### 问题：缺少关键信息

**解决方案**: AI 会标注"缺失信息"，根据提示补充需求后重新调用 skill。

## 与 Agent 的配合

这个 skill 可以与已有的 `ai-prompt-translator` agent 配合使用：

1. **Skill**: 生成技术规范和执行指令
2. **Agent**: 执行具体的开发任务

或者：

1. **Slash Command**: 快速调用 skill
2. **自动触发 Agent**: skill 输出后自动启动 agent 执行

---

**提示**: 这个 skill 的价值在于将模糊的想法转化为可执行的技术规范，节省架构设计时间，确保技术决策的严谨性。对于任何非平凡的项目，都建议先使用这个 skill 进行规划设计喵～ ฅ'ω'ฅ
