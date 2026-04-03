# ComfyUI 各架构 JSON 模板与选型指南

> Phase 4 生成 JSON 时参考此文件中的模板片段和架构选型原则。

---

## 架构选型决策树（约 2025–2026，ComfyUI 生态）

> 排序是**场景化倾向**，不是绝对天梯；具体以用户 VRAM、许可、已装节点与当时模型评测为准。

```
用户需求
│
├─► 视频生成？
│   └─► 是 → Wan 2.1 / CogVideoX / AnimateDiff（与静图工作流分开设计）
│
├─► 动漫/二次元专精？
│   └─► 是 → NoobAI XL / Illustrious XL / AniShadow（SDXL 生态仍最丰富）
│
├─► 画面内文字 / 多语 / 强 prompt 遵循（且显存够）？
│   └─► 是 → 检索当时评测：Qwen-Image、SD3.5、FLUX.2 等谁更占优
│
├─► 极致写实 / 商业级静图（高 VRAM、可取得权重）？
│   └─► 是 → FLUX.2（开放权重 Dev 等）、SD3.5 Large、Qwen-Image（择一并查 ComfyUI 示例）
│
├─► 要低 VRAM 或极快出图？
│   └─► 是 → Z-Image 等轻量 DiT · SD3.5 Turbo · FLUX.1-schnell（fp8/GGUF）· SD 1.5
│
├─► 要最多现成模板、最少踩坑？
│   └─► 是 → FLUX.1-dev (fp8) 或 SD3.5（ComfyUI_examples 有官方范例）
│
└─► 通用 XL 兜底？
    └─► DreamShaper XL / RealVisXL / CinematicXL
```

### 2026 年前后补充架构速览（与 FLUX.1 并列认知）

| 架构 | 要点 | ComfyUI 注意 |
|------|------|----------------|
| **FLUX.2** | BFL 新一代，开放权重 Dev 等；rectified flow / 大参数量 | 节点与量化格式随版本更新，生成前对照官方/社区最新 workflow |
| **SD3.5** | MMDiT，多编码器（CLIP-L/G + T5）；Large / Turbo 等变体 | 参考 [ComfyUI SD3 官方示例](https://comfyanonymous.github.io/ComfyUI_examples/sd3/) |
| **Qwen-Image** | 多模态 DiT，图文与多语场景强；全精度显存高 | 优先查 HuggingFace + 是否有 GGUF/量化与对应 custom nodes |
| **Z-Image** | 单流 DiT，参数量相对小，适合效率向部署 | 节点名以用户环境为准，勿假设与 SDXL 同图 |

**权重格式**：GGUF、FP8、NVFP4（RTX 50 系等）按显卡与 ComfyUI 支持选择；8–16GB VRAM 常需量化版。

---

## FLUX.1 架构

### 特点
- DiT（Diffusion Transformer）架构，全注意力机制
- 文本理解能力强，prompt following 优秀
- 需要 T5XXL + CLIP-L 双文本编码器
- fp8 量化版本（8位浮点）约需 8GB VRAM
- 推荐分辨率：1024×1024，1360×768，768×1360，832×1216

### 主流模型
| 模型 | 用途 | 文件名参考 |
|------|------|-----------|
| FLUX.1-dev (fp8) | 高质量生成 | `flux1Dev8x8E4m3fn.safetensors` |
| FLUX.1-schnell | 快速生成（4步） | `flux1-schnell-fp8.safetensors` |
| Chroma | FLUX 变体，艺术风格 | `chroma-unlocked-v35.safetensors` |
| Illustrious FLUX | 动漫 FLUX 微调 | 见 CivitAI |

### 标准管线 JSON 片段（FLUX.1 一体化 checkpoint 版）

```json
{
  "last_node_id": 9,
  "last_link_id": 12,
  "nodes": [
    {
      "id": 1, "type": "CheckpointLoaderSimple",
      "pos": [100, 150], "size": {"0": 315, "1": 98},
      "flags": {}, "order": 0, "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
        {"name": "CLIP", "type": "CLIP", "links": [3, 4], "slot_index": 1},
        {"name": "VAE", "type": "VAE", "links": [10], "slot_index": 2}
      ],
      "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
      "widgets_values": ["flux1Dev8x8E4m3fn.Dkyf.safetensors"]
    },
    {
      "id": 2, "type": "CLIPTextEncode",
      "pos": [450, 50], "size": {"0": 400, "1": 200},
      "flags": {}, "order": 2, "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": 3}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5], "slot_index": 0}],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": ["a beautiful woman in a garden, detailed, 8k, cinematic lighting"]
    },
    {
      "id": 3, "type": "CLIPTextEncode",
      "pos": [450, 280], "size": {"0": 400, "1": 200},
      "flags": {}, "order": 3, "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": 4}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "slot_index": 0}],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": ["blurry, low quality, watermark, text"]
    },
    {
      "id": 4, "type": "EmptyLatentImage",
      "pos": [100, 350], "size": {"0": 315, "1": 106},
      "flags": {}, "order": 1, "mode": 0,
      "inputs": [],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
      "properties": {"Node name for S&R": "EmptyLatentImage"},
      "widgets_values": [1024, 1024, 1]
    },
    {
      "id": 5, "type": "KSampler",
      "pos": [900, 150], "size": {"0": 315, "1": 262},
      "flags": {}, "order": 5, "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "positive", "type": "CONDITIONING", "link": 5},
        {"name": "negative", "type": "CONDITIONING", "link": 6},
        {"name": "latent_image", "type": "LATENT", "link": 7}
      ],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [8], "slot_index": 0}],
      "properties": {"Node name for S&R": "KSampler"},
      "widgets_values": [42, "fixed", 20, 3.5, "euler", "simple", 1.0]
    },
    {
      "id": 6, "type": "VAEDecode",
      "pos": [1280, 150], "size": {"0": 210, "1": 46},
      "flags": {}, "order": 6, "mode": 0,
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": 8},
        {"name": "vae", "type": "VAE", "link": 10}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [11], "slot_index": 0}],
      "properties": {"Node name for S&R": "VAEDecode"},
      "widgets_values": []
    },
    {
      "id": 7, "type": "SaveImage",
      "pos": [1550, 150], "size": {"0": 315, "1": 270},
      "flags": {}, "order": 7, "mode": 0,
      "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
      "outputs": [],
      "properties": {"Node name for S&R": "SaveImage"},
      "widgets_values": ["ComfyUI"]
    }
  ],
  "links": [
    [1, 1, 0, 5, 0, "MODEL"],
    [3, 1, 1, 2, 0, "CLIP"],
    [4, 1, 1, 3, 0, "CLIP"],
    [5, 2, 0, 5, 1, "CONDITIONING"],
    [6, 3, 0, 5, 2, "CONDITIONING"],
    [7, 4, 0, 5, 3, "LATENT"],
    [8, 5, 0, 6, 0, "LATENT"],
    [10, 1, 2, 6, 1, "VAE"],
    [11, 6, 0, 7, 0, "IMAGE"]
  ],
  "groups": [],
  "config": {},
  "extra": {"ds": {"scale": 1.0, "offset": [0, 0]}},
  "version": 0.4
}
```

---

## SDXL / NoobAI XL / Illustrious XL 架构

### 特点
- 基于 SDXL 1.0 基础架构的微调模型
- NoobAI XL / Illustrious XL：高质量动漫/二次元专精
- 推荐分辨率：1024×1024, 896×1152, 1152×896, 832×1216
- 支持标准 LoRA（SDXL 格式）

### 主流模型（截至 2025）
| 模型 | 风格 | CivitAI |
|------|------|---------|
| NoobAI XL v1.0.5 | 动漫/二次元 | civitai.com/models/833294 |
| Illustrious XL v0.1 | 动漫高质量 | civitai.com/models/795765 |
| DreamShaper XL | 通用/幻想 | civitai.com/models/112902 |
| RealVisXL V5.0 | 写实 | civitai.com/models/139562 |
| CinematicXL | 电影感 | civitai.com |

### 标准 SDXL t2i 管线 JSON 片段（含 LoRA）

```json
{
  "last_node_id": 10,
  "last_link_id": 15,
  "nodes": [
    {
      "id": 1, "type": "CheckpointLoaderSimple",
      "pos": [100, 100], "size": {"0": 315, "1": 98},
      "flags": {}, "order": 0, "mode": 0,
      "inputs": [],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
        {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
        {"name": "VAE", "type": "VAE", "links": [12], "slot_index": 2}
      ],
      "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
      "widgets_values": ["noobaiXLNAIXL_v105Version.safetensors"]
    },
    {
      "id": 10, "type": "LoraLoader",
      "pos": [480, 100], "size": {"0": 315, "1": 126},
      "flags": {}, "order": 2, "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 1},
        {"name": "clip", "type": "CLIP", "link": 2}
      ],
      "outputs": [
        {"name": "MODEL", "type": "MODEL", "links": [13], "slot_index": 0},
        {"name": "CLIP", "type": "CLIP", "links": [14, 15], "slot_index": 1}
      ],
      "properties": {"Node name for S&R": "LoraLoader"},
      "widgets_values": ["your_lora_name.safetensors", 1.0, 1.0]
    },
    {
      "id": 2, "type": "CLIPTextEncode",
      "pos": [860, 50], "size": {"0": 400, "1": 200},
      "flags": {}, "order": 3, "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": 14}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5], "slot_index": 0}],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": ["masterpiece, best quality, 1girl, solo, detailed face, soft lighting"]
    },
    {
      "id": 3, "type": "CLIPTextEncode",
      "pos": [860, 280], "size": {"0": 400, "1": 200},
      "flags": {}, "order": 4, "mode": 0,
      "inputs": [{"name": "clip", "type": "CLIP", "link": 15}],
      "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6], "slot_index": 0}],
      "properties": {"Node name for S&R": "CLIPTextEncode"},
      "widgets_values": ["worst quality, low quality, blurry, watermark, text, deformed"]
    },
    {
      "id": 4, "type": "EmptyLatentImage",
      "pos": [100, 320], "size": {"0": 315, "1": 106},
      "flags": {}, "order": 1, "mode": 0,
      "inputs": [],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
      "properties": {"Node name for S&R": "EmptyLatentImage"},
      "widgets_values": [1024, 1024, 1]
    },
    {
      "id": 5, "type": "KSampler",
      "pos": [1320, 150], "size": {"0": 315, "1": 262},
      "flags": {}, "order": 5, "mode": 0,
      "inputs": [
        {"name": "model", "type": "MODEL", "link": 13},
        {"name": "positive", "type": "CONDITIONING", "link": 5},
        {"name": "negative", "type": "CONDITIONING", "link": 6},
        {"name": "latent_image", "type": "LATENT", "link": 7}
      ],
      "outputs": [{"name": "LATENT", "type": "LATENT", "links": [8], "slot_index": 0}],
      "properties": {"Node name for S&R": "KSampler"},
      "widgets_values": [42, "fixed", 28, 7.0, "dpmpp_2m", "karras", 1.0]
    },
    {
      "id": 6, "type": "VAEDecode",
      "pos": [1700, 150], "size": {"0": 210, "1": 46},
      "flags": {}, "order": 6, "mode": 0,
      "inputs": [
        {"name": "samples", "type": "LATENT", "link": 8},
        {"name": "vae", "type": "VAE", "link": 12}
      ],
      "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [11], "slot_index": 0}],
      "properties": {"Node name for S&R": "VAEDecode"},
      "widgets_values": []
    },
    {
      "id": 7, "type": "SaveImage",
      "pos": [1970, 150], "size": {"0": 315, "1": 270},
      "flags": {}, "order": 7, "mode": 0,
      "inputs": [{"name": "images", "type": "IMAGE", "link": 11}],
      "outputs": [],
      "properties": {"Node name for S&R": "SaveImage"},
      "widgets_values": ["ComfyUI"]
    }
  ],
  "links": [
    [1, 1, 0, 10, 0, "MODEL"],
    [2, 1, 1, 10, 1, "CLIP"],
    [5, 2, 0, 5, 1, "CONDITIONING"],
    [6, 3, 0, 5, 2, "CONDITIONING"],
    [7, 4, 0, 5, 3, "LATENT"],
    [8, 5, 0, 6, 0, "LATENT"],
    [11, 6, 0, 7, 0, "IMAGE"],
    [12, 1, 2, 6, 1, "VAE"],
    [13, 10, 0, 5, 0, "MODEL"],
    [14, 10, 1, 2, 0, "CLIP"],
    [15, 10, 1, 3, 0, "CLIP"]
  ],
  "groups": [],
  "config": {},
  "extra": {"ds": {"scale": 1.0, "offset": [0, 0]}},
  "version": 0.4
}
```

---

## SD 1.5 架构

### 特点
- 最广泛兼容性，大量 LoRA 可用
- 512×512 或 768×768 原生分辨率
- VAE 需要单独加载（推荐 vae-ft-mse-840000）

### 管线结构
与 SDXL 完全相同的节点拓扑，差异点：
- `EmptyLatentImage` 使用 512×768 或 768×512
- KSampler 推荐：steps=20, cfg=7.0, sampler=euler_a, scheduler=normal
- 通常需要 `CLIPSetLastLayer`（stop_at=-2）

---

## img2img 管线扩展

在标准管线基础上，替换 `EmptyLatentImage` 为：

```json
{
  "id": 20, "type": "LoadImage",
  "pos": [100, 300], "size": {"0": 315, "1": 110},
  "flags": {}, "order": 0, "mode": 0,
  "inputs": [],
  "outputs": [
    {"name": "IMAGE", "type": "IMAGE", "links": [20], "slot_index": 0},
    {"name": "MASK", "type": "MASK", "links": [], "slot_index": 1}
  ],
  "properties": {"Node name for S&R": "LoadImage"},
  "widgets_values": ["input_image.png", "image"]
},
{
  "id": 21, "type": "VAEEncode",
  "pos": [480, 300], "size": {"0": 210, "1": 46},
  "flags": {}, "order": 2, "mode": 0,
  "inputs": [
    {"name": "pixels", "type": "IMAGE", "link": 20},
    {"name": "vae", "type": "VAE", "link": 12}
  ],
  "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
  "properties": {"Node name for S&R": "VAEEncode"},
  "widgets_values": []
}
```

同时将 KSampler 的 `denoise` 改为 0.5–0.8（根据改变程度调整）。

---

## Hires Fix 管线扩展

在 VAEDecode 之后，保存之前，添加：

```json
（KSampler → VAEDecode 之后插入）
→ ImageScale (bicubic, 2x) → VAEEncode → KSampler (denoise=0.4) → VAEDecode → SaveImage
```

或使用 latent 空间：

```json
KSampler → LatentUpscale (bilinear, 2x) → KSampler (denoise=0.4) → VAEDecode → SaveImage
```

---

## 常用 KSampler 参数推荐

| 场景 | steps | cfg | sampler | scheduler | denoise |
|------|-------|-----|---------|-----------|---------|
| FLUX.1-dev t2i | 20 | 3.5 | euler | simple | 1.0 |
| FLUX.1-schnell | 4 | 1.0 | euler | simple | 1.0 |
| SDXL/NoobXL t2i | 28 | 7.0 | dpmpp_2m | karras | 1.0 |
| SD 1.5 t2i | 20 | 7.0 | euler_ancestral | normal | 1.0 |
| img2img (轻改) | 20 | 7.0 | dpmpp_2m | karras | 0.5 |
| img2img (重改) | 25 | 7.0 | dpmpp_2m | karras | 0.75 |
| Hires Fix | 15 | 7.0 | dpmpp_2m | karras | 0.4 |

---

## CivitAI 模型查询策略

当需要查找最新模型时，使用以下搜索方式：
1. CivitAI API：`https://civitai.com/api/v1/models?sort=Highest%20Rated&period=Month&types=Checkpoint`
2. 搜索关键词：`site:civitai.com [style] [architecture] 2026`（或 `2025` 作补充）
3. HuggingFace：`https://huggingface.co/models?sort=trending&search=[architecture]`

查询时重点关注：
- **下载量 + 近30天活跃度**（表示社区验证质量）
- **基础架构标签**（SDXL / FLUX.1 / SD3.5）
- **ComfyUI 兼容性**（是否有节点支持说明）
