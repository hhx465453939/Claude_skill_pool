---
name: code-debugger
description: 基于深度上下文理解的代码调试与增量开发流程。用于修复 Bug、性能问题、变量追踪或在既有模块上做增量功能时，需要建立调用链/变量依赖并维护 `.debug/` 记录的场景。
---

# Code Debugger

## Overview

在修改代码前先建立完整上下文关系网络，最小化变更并记录可追溯的调试文档，确保修复可验证、可回滚、可复盘。

## 开发环境与运行上下文（优先确认）

在**执行验证、测试或 Checkfix 之前**，务必确认项目的「部署-开发」架构，避免在错误环境中跑命令导致死循环或无法推进：

- **常见形态**：本机 Windows 开发；WSL 内开发；**内网 NAS 或云服务器**上代码通过 Samba 挂载到 Windows 盘符，在本地 IDE 编辑，但**实际运行/测试需 SSH 登录远程执行**。
- **若无法从仓库或路径推断**：主动问开发者一句，例如：「项目是否在 NAS/Samba+SSH 或远程服务器上开发？当前是怎么跑测试/构建的？」
- **若是远程/NAS-Samba+SSH 形态**：
  - 询问是否已有现成的 SSH 登录方式（如 `ssh nas`、`ssh dev` 等别名或主机配置）。
  - 若无，则指导用户建立公钥-私钥登录（`ssh-keygen` + 将公钥写入远程 `~/.ssh/authorized_keys`），并确认**项目在远程机器上的实际路径**（如 `/mnt/dev/xxx`、`/home/user/proj`）。
  - 后续验证与 Checkfix 的 shell 命令应在该上下文中执行（例如 `ssh nas "cd /mnt/dev/xxx && cargo test"`），而不是在本地 Samba 映射路径下直接执行，以保障调试流畅、节省成本并防止 AI 反复无效尝试。
- **首次与用户确认后，将上述判断结果写入当前模块的 .debug 文档，作为「运行上下文/测试规则」**（运行环境类型、SSH 方式、远程项目路径、验证/Checkfix 执行方式等）。**后续再调用本命令时，优先从 .debug 读取该规则，不再反复询问。**

## Workflow

### 1. 上下文构建
- 解析用户任务，识别涉及模块与边界。
- 使用 `rg`/文件浏览定位入口与相关模块，梳理调用链、变量依赖和数据流向。
- 检查 `.debug/`：若已有同模块记录则加载；若模块不同则新建，避免混杂上下文。
- 评估影响范围与潜在回归点，只改必要代码。

### 2. 问题定位与实施
- 基于上下文网络定位根因，给出 1-2 个方案并评估风险。
- 采用最小改动原则实施修复或增量功能，保持现有架构与风格一致。
- 添加必要的边界检查和错误处理。

### 3. 验证与记录
- 运行现有测试或提供明确的手动验证步骤。
- **Debug-Checkfix 闭环（必选）**：完成代码修改后，根据项目技术栈执行相应的自动检查（见下方「技术栈与推荐检查」），将「修复 → 检查 → 修正」形成闭环；检查结果纳入验证并写入 `.debug/`。
- 更新 `.debug/` 记录：问题、根因、变更、验证（含 checkfix 结果）、影响评估。
- 根据反馈迭代修复与文档。

### 技术栈与推荐检查（Checkfix 闭环）

读取本 skill 的编程工具应在 debug 完成后**自动考虑**执行下列检查，减少开发者反复提醒的负担：

| 技术栈/类型 | 推荐检查 | 说明 |
|-------------|----------|------|
| Python | `ruff check .`、`ruff format --check .` 或 `black --check .` | 先 lint 再 format；失败则修复后复跑 |
| 前端 (Node/npm) | `npm install`（依赖变更时）、`npm run lint` 或 `npx eslint .`，可选 `npm run build` | 依赖与静态检查，优先用 package.json scripts |
| Rust | `cargo check` 或 `cargo clippy` | 编译与 Clippy |
| Go | `go build ./...`、`gofmt -l .` 或 `golangci-lint run` | 编译与格式/静态检查 |
| Java/Kotlin (Maven) | `mvn compile` 或 `mvn verify` | 编译与测试 |
| Java/Kotlin (Gradle) | `./gradlew compileJava` 或 `./gradlew check` | 同上 |
| C# / .NET | `dotnet build`、`dotnet format --verify-no-changes` | 编译与格式 |
| 通用 | 项目内已配置的 lint/format/check 脚本（如 `make check`、`invoke lint`） | 优先执行项目既有脚本 |

**执行原则**：识别技术栈后，至少执行一类检查（lint/format/build）；若检查失败，当轮内修复并复跑直至通过或记录为技术债；结果写入验证与 .debug 记录。

## .debug 文档规则

### 目录与命名
- 统一放在 `.debug/`。
- 每个功能模块单独一份：`.debug/<module>-debug.md`。

### 模块隔离
- 交叉度计算：`(共享函数数 + 共享变量数 + 共享数据结构数) / 总组件数`。
- 交叉度 > 30%：合并到现有文档。
- 交叉度 < 30%：新建文档。

### 推荐模板（精简版）

```markdown
# [模块] Debug 记录

## 元信息
- 模块名称:
- 创建时间:
- 最后更新:
- 相关文件:
- 依赖模块:

## 运行上下文与测试规则（首次确认后填写，后续优先读取此处，不再反复询问）
- 运行环境: [本机 Windows / WSL / NAS-Samba+SSH 或远程]
- SSH 方式（若远程）: [如 ssh nas、ssh user@host]
- 远程项目路径（若远程）: [如 /mnt/dev/xxx]
- 验证/Checkfix 执行方式: [如：在本地终端执行 / ssh nas "cd /mnt/dev/xxx && ..."]

## 上下文关系网络
- 文件结构
- 函数调用链
- 变量依赖图
- 数据流向

## Debug 历史
### [YYYY-MM-DD HH:MM] [任务标题]
- 问题描述
- 根因定位
- 解决方案
- 代码变更（文件/函数）
- 验证结果
- 影响评估

## 待追踪问题
## 技术债务记录
## 架构决策记录（可选）
```

## Response Format (recommended)

在开始与完成任务时，优先用以下结构输出关键信息：

```markdown
## 任务分析
## 开发环境/运行上下文
[本机 / WSL / NAS-Samba+SSH 或远程；若远程，SSH 方式与项目路径如 /mnt/dev/xxx]
## 上下文探索
## .debug 文档状态
## 执行方案
## 更新记录
```
