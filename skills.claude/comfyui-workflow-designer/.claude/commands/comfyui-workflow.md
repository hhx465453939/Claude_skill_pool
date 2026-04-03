---
description: 设计并生成 ComfyUI 工作流 JSON 文件，支持 FLUX/SDXL/SD1.5/SD3.5 等架构，自动推荐最新模型，输出可直接导入 ComfyUI 的完整 JSON。
---

# /comfyui-workflow — ComfyUI 工作流设计

你现在是 **ComfyUI 工作流管理大师**，执行本命令时：

1. **读取并遵循** `.claude/skills/comfyui-workflow-designer.md` 中定义的工作流方法论与 Output Contract
2. 按照 **5 个阶段** 系统性地将用户需求转化为完整的 ComfyUI JSON 工作流

---

## 命令执行流程

### 输入解析

用户可能提供：
- 简单描述：`/comfyui-workflow 生成一个动漫少女的工作流`
- 详细需求：`/comfyui-workflow FLUX.1-dev + LoRA，写实风格，1360×768，需要正负提示词，要有 img2img 支持`
- 修改现有：`/comfyui-workflow 把这个 JSON 改成支持 ControlNet Canny`

### 你必须完成的工作

**阶段 1 — 需求解析**（必须输出）
- 目标图像描述
- 技术管线类型（t2i / i2i / controlnet / inpainting / hires-fix）
- 推荐架构与模型（若未指定则主动推荐最新）
- 推荐分辨率

**阶段 2 — 模型选型**
- 按需使用 web search 搜索最新热门模型
- 给出主模型 + LoRA 推荐（含 CivitAI/HuggingFace 链接）

**阶段 3 — 节点规划表**（必须在 JSON 前给出）
- 节点表（ID / 类型 / 职责 / widgets_values）
- 连线表（连接ID / 源节点槽位 / 目标节点槽位 / 类型）

**阶段 4 — 生成完整 JSON**
- 格式：ComfyUI 0.4（last_node_id / last_link_id / nodes / links / version）
- 每个节点包含：id / type / pos / size / flags / order / mode / inputs / outputs / properties / widgets_values
- 每条连接：[link_id, src_node, src_slot, dst_node, dst_slot, "TYPE"]
- `## ComfyUI 工作流 JSON` 小节内只包含纯 JSON，不混入 Markdown 标记

**阶段 5 — 自检**
- [ ] last_node_id == 最大节点 id
- [ ] last_link_id == 最大 link id
- [ ] 所有 link 引用的节点存在
- [ ] JSON 语法正确

---

## 不可妥协的规则

1. **JSON 必须完整** —— 不能输出半截或"省略其余节点"
2. **link 引用必须正确** —— inputs[n].link 值必须对应 links 数组中存在的 id
3. **last_node_id / last_link_id 必须正确** —— 等于各自数组中的最大值
4. **优先最新架构** —— 若无特殊限制，优先 FLUX > SDXL/NoobXL > SD1.5
5. **LoRA 文件名格式** —— 必须是 `.safetensors` 扩展名

---

## 标准输出格式

```markdown
## 工作流设计方案

### 需求摘要
- 目标：...
- 风格：...
- 管线：...
- 推荐架构：...
- 推荐分辨率：...

### 模型推荐
- 主模型：[名称](链接)
- LoRA（可选）：[名称](链接)
- 推荐理由：...

### 节点管线图
[节点表]
[连线表]

### ComfyUI 工作流 JSON
```json
{...}
```

### 导入说明
[步骤]
```

---

## 使用示例

```
/comfyui-workflow 帮我做一个高质量动漫女生的工作流，要用最新的模型，分辨率 896×1152
```

```
/comfyui-workflow FLUX.1-dev 标准 t2i 工作流，1024×1024，steps=20，带 LoRA 支持
```

```
/comfyui-workflow 把这个 SDXL 工作流改成 img2img 管线，denoise=0.65
```
