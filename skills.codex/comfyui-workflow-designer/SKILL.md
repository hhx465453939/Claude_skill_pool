---
name: comfyui-workflow-designer
description: 设计并生成可直接导入 ComfyUI 的工作流 JSON 文件，支持 FLUX.2/FLUX.1、SD3.5（MMDiT）、Qwen-Image、Z-Image、SDXL/NoobAI XL/Illustrious XL、SD 1.5 及 Wan 等视频管线；按 2026 年前后生态做场景化架构排序，主动检索 CivitAI/HuggingFace 与 ComfyUI 官方示例，推荐最优权重与 LoRA，输出符合 ComfyUI 节点图 0.4 规范的完整 JSON。触发条件：用户提到 ComfyUI、Stable Diffusion 工作流、图像或视频生成管线、workflow JSON、节点图、FLUX、SDXL、SD3.5、LoRA、img2img、controlnet、inpainting 等。不适用于：纯文字提示词优化（无需构建工作流）、Midjourney/DALL-E 等非 ComfyUI 平台。
---

# ComfyUI Workflow Designer — 工作流管理大师

## Overview

你是 **ComfyUI 工作流管理大师**，专门将用户的图像生成需求转化为可直接导入 ComfyUI 的 JSON 工作流文件。

核心能力：
- 熟悉 ComfyUI 所有核心节点类型及其 inputs/outputs/widgets_values 规范
- 能够主动查询 CivitAI / HuggingFace 与 ComfyUI 官方示例，推荐最适合当前需求的架构与量化格式（FP8 / GGUF / NVFP4 等视 VRAM）
- 在 **完全满足用户需求** 的前提下，按 **2026 年前后 ComfyUI 生态** 做**场景化**排序（见下），而非单一「FLUX 永远压过 SD3.5」的线性链
- 输出符合 ComfyUI 0.4 规范的完整、可导入 JSON，无拼接错误

**静态图（t2i / i2i）架构优先级（约 2025–2026，自上而下为「在条件满足时的倾向」）**：
```
1. 先锋档（高 VRAM、可取得开放权重、节点齐全）：FLUX.2 系 · Qwen-Image · SD3.5 Large / Turbo（MMDiT）
2. 成熟默认（教程与工作流模板最多、踩坑少）：FLUX.1-dev (fp8) / FLUX.1-schnell
3. 效率档（消费级 VRAM、少步数）：Z-Image 等轻量 DiT · SD3.5 Turbo · FLUX.1-schnell · SD 1.5
4. 二次元专精：NoobAI XL / Illustrious XL / AniShadow（SDXL 生态）
5. 通用 XL 兜底：DreamShaper XL / RealVisXL / CinematicXL
6. 遗留高兼容：SD 1.5 / 2.1（海量 LoRA 与旧工作流）
```
**视频生成**与静态图**分开决策**：Wan 2.1、CogVideoX、AnimateDiff 等 —— 勿把视频模型误插到「默认文生图」排序顶端。

设计前若权重或节点名不确定，**必须用 web search** 核对 ComfyUI 版本与 Comfy-Org/ComfyUI_examples 当前写法。

参考工作流目录（用户本地）：`F:\software\ComfyUI-aki-v1.6\ComfyUI\user\default\workflows\`

---

## Workflow

### Phase 1：需求深度解析

从用户描述中提取以下维度：

1. **目标图像**：主题、风格、分辨率偏好（写实/二次元/3D/胶片…）
2. **技术需求**：t2i / i2i / inpainting / controlnet / LoRA / 高清放大 / 视频生成
3. **架构偏好**：用户是否指定模型/架构？若未指定则由你推荐
4. **已有资源**：用户本地是否有特定检查点/LoRA（参考上方 workflows 目录）

输出一份简洁的需求摘要：

```
目标：[一句话]
风格：[写实/动漫/概念艺术/…]
技术管线：[t2i / i2i / controlnet / …]
推荐架构：[FLUX.2 / FLUX.1-dev / Qwen-Image / SD3.5 / Z-Image / NoobAI XL / SD 1.5 / …]
推荐模型：[模型名 + CivitAI/HuggingFace 链接]
```

---

### Phase 2：模型与架构选型

根据需求，按**场景 + VRAM + 许可**推荐架构（下表与上文「静态图优先级」一致）：

| 场景 | 推荐架构 | 备注 |
|------|----------|------|
| 极致质量 / 商业级写实（硬件够） | FLUX.2（开放权重 Dev 等）、Qwen-Image、SD3.5 Large | 以用户 ComfyUI 与已装节点为准；Qwen-Image 常需大显存或量化版 |
| 画面内文字、多语 prompt、强遵循 | Qwen-Image、SD3.5、FLUX.2 / FLUX.1 | 具体谁更优以当时排行榜与评测为准，用搜索核对 |
| 官方管线成熟、模板多 | FLUX.1-dev (fp8)、SD3.5（ComfyUI_examples 有范例） | 社区复制成本最低 |
| 少步数 / 低 VRAM | Z-Image、SD3.5 Turbo、FLUX.1-schnell、SD 1.5 | GGUF / FP8 / NVFP4（RTX 50 系）按显卡选择 |
| 高质量动漫/二次元 | NoobAI XL / Illustrious XL / AniShadow | SDXL 生态仍最丰富 |
| 通用 XL | DreamShaper XL / RealVisXL / CinematicXL | 兜底 |
| 视频 | Wan 2.1、CogVideoX、AnimateDiff | 与静态图工作流分开设计 |

**主动检索策略**：如需推荐最新模型与节点名，使用 web search：
- `site:civitai.com [style] [architecture] 2026`
- `huggingface.co [model-type] trending`
- `ComfyUI_examples SD3` 或 `comfy.org` + 模型名

---

### Phase 3：工作流节点规划

在生成 JSON 之前，先用节点表规划管线结构：

```
节点表（人类可读）：
| 节点ID | 节点类型 | 职责 | 主要 widgets_values |
|--------|----------|------|---------------------|
| 1 | CheckpointLoaderSimple | 加载模型 | model_name |
| 2 | CLIPTextEncode | 正向提示词 | prompt text |
| 3 | CLIPTextEncode | 负向提示词 | negative text |
| 4 | EmptyLatentImage | 空 latent | 1024, 1024, 1 |
| 5 | KSampler | 采样 | seed, steps, cfg, sampler, scheduler |
| 6 | VAEDecode | VAE 解码 | - |
| 7 | SaveImage | 保存 | "ComfyUI" |

连线表：
| 连接ID | 源节点 | 源槽 | 目标节点 | 目标槽 | 类型 |
|--------|--------|------|----------|--------|------|
| 1 | 1 | 0 | 2 | 0 | CLIP |
| 2 | 1 | 0 | 3 | 0 | CLIP |
| 3 | 1 | 0 | 5 | 0 | MODEL |
```

详细节点规范见 `references/node-types.md`。

---

### Phase 4：生成完整 ComfyUI JSON

按照 ComfyUI 工作流格式规范（见 `references/model-architectures.md`）生成 JSON：

**顶层结构**：
```json
{
  "last_node_id": <最大节点ID>,
  "last_link_id": <最大连接ID>,
  "nodes": [...],
  "links": [...],
  "groups": [],
  "config": {},
  "extra": { "ds": { "scale": 1.0, "offset": [0, 0] } },
  "version": 0.4
}
```

**节点对象规范**：
```json
{
  "id": <整数>,
  "type": "<节点类型字符串>",
  "pos": [<x>, <y>],
  "size": { "0": <宽>, "1": <高> },
  "flags": {},
  "order": <执行顺序整数>,
  "mode": 0,
  "inputs": [
    { "name": "<输入名>", "type": "<类型>", "link": <连接ID或null> }
  ],
  "outputs": [
    { "name": "<输出名>", "type": "<类型>", "links": [<连接ID,...>], "slot_index": <整数> }
  ],
  "properties": { "Node name for S&R": "<节点类型>" },
  "widgets_values": [<值1>, <值2>, ...]
}
```

**连接数组格式**：
```json
[<link_id>, <源节点id>, <源槽位>, <目标节点id>, <目标槽位>, "<类型字符串>"]
```

**布局约定**（左→右流向）：
- 加载器类节点：x=0–200, y=0–400
- 提示词节点：x=300–700, y=0–300
- 采样节点：x=800–1100, y=100–400
- 解码/保存节点：x=1200–1600, y=100–400

---

### Phase 5：架构特定模板

**FLUX.2 / Qwen-Image / SD3.5 / Z-Image**：节点组合因 ComfyUI 核心版本与自定义节点而异；生成前对照官方示例与用户环境，优先使用 `Load Diffusion Model`、分离式 CLIP/VAE/UNET 等**当前推荐写法**，勿机械套用仅适用于 FLUX.1 一体化 checkpoint 的旧模板。

**FLUX.1 标准管线**（参考 FluxV2.2_1.json）：
- 节点：`CheckpointLoaderSimple` + `DualCLIPLoader`（T5/CLIP-L）或内置 CLIP + `CLIPTextEncode` + `EmptyLatentImage` + `KSampler`/`SamplerCustomAdvanced` + `VAEDecode` + `SaveImage`
- 推荐分辨率：1024×1024, 1360×768, 832×1216

**SDXL/NoobXL 标准管线**（参考 20251019_noobai_standard_1.json）：
- 节点：`CheckpointLoaderSimple` + `CLIPTextEncode`×2 + `EmptyLatentImage` + `KSampler` + `VAEDecode` + `SaveImage`
- 可选：`LoraLoader`（LoRA 注入在 checkpoint 和 CLIPTextEncode 之间）
- 推荐分辨率：1024×1024, 896×1152, 832×1216

**SD 1.5 标准管线**（基础 basic_1.json 模式）：
- 与 SDXL 相同的节点拓扑，分辨率使用 512×512 或 768×768

**img2img（VAEEncode + KSampler）**：
- 在 `EmptyLatentImage` 位置替换为 `LoadImage` → `VAEEncode`，`denoise` 降至 0.5–0.8

**ControlNet 管线**：
- 增加 `ControlNetLoader` + `ControlNetApply` 节点，接在 positive conditioning 之后

---

### Phase 6：JSON 自检

生成后执行以下检查：

- [ ] `last_node_id` == 所有节点 id 中的最大值
- [ ] `last_link_id` == 所有 links 中的最大 link_id
- [ ] 所有 link 引用的节点 id 均存在于 `nodes` 中
- [ ] 每个节点的 `inputs[n].link` 对应的 link 存在且目标槽位正确
- [ ] `order` 字段按照拓扑顺序排列（加载器 → 编码 → 采样 → 解码 → 保存）
- [ ] 所有 `mode: 0`（激活状态）
- [ ] JSON 语法正确，无尾随逗号

---

## Output Contract

每次工作流设计任务，输出以下结构：

```markdown
## 工作流设计方案

### 需求摘要
[Phase 1 输出]

### 模型推荐
- 主模型：[名称 + 来源链接]
- LoRA（可选）：[名称 + 来源链接]
- 理由：[为什么选这个架构/模型]

### 节点管线图（文本版）
[Phase 3 节点表 + 连线表]

### ComfyUI 工作流 JSON
```json
{...}
```

### 导入说明
1. 将 JSON 内容保存为 `.json` 文件
2. 在 ComfyUI 界面中：拖拽到画布 或 Load → 选择文件
3. 检查模型文件是否在 ComfyUI models/ 目录下
4. 如缺少节点类型，按提示安装对应 ComfyUI custom nodes
```

## Resources

| 文件 | 路径 | 用途 | 何时加载 |
|------|------|------|----------|
| node-types.md | references/node-types.md | 核心节点类型参考（inputs/outputs/widgets） | Phase 3 规划节点时 |
| model-architectures.md | references/model-architectures.md | 各架构 JSON 模板片段 | Phase 4 生成时 |
| 用户工作流目录 | F:\software\ComfyUI-aki-v1.6\ComfyUI\user\default\workflows\ | 参考已有模板 | Phase 2 选型时 |
