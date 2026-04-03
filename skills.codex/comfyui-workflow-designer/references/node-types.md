# ComfyUI 核心节点类型参考

> 本文档记录 ComfyUI 内置节点的标准 inputs / outputs / widgets_values 规范。
> 每次 Phase 3 规划节点时查阅，确保槽位映射和 widgets_values 顺序正确。

---

## 通用节点（所有架构）

### CheckpointLoaderSimple
- **职责**：加载 .safetensors 检查点（含 MODEL + CLIP + VAE）
- **inputs**：无连线输入
- **outputs**：`[0] MODEL`, `[1] CLIP`, `[2] VAE`
- **widgets_values**：`[checkpoint_filename_string]`
- **节点尺寸参考**：315×98

### VAELoader
- **职责**：加载独立 VAE 文件
- **inputs**：无
- **outputs**：`[0] VAE`
- **widgets_values**：`[vae_filename_string]`

### CLIPTextEncode
- **职责**：将文本提示词编码为 CONDITIONING
- **inputs**：`[0] clip (CLIP)`
- **outputs**：`[0] CONDITIONING`
- **widgets_values**：`[prompt_text_string]`
- **节点尺寸参考**：400×200

### CLIPSetLastLayer
- **职责**：裁剪 CLIP 最后 N 层（用于 SD 1.5 兼容性）
- **inputs**：`[0] clip (CLIP)`
- **outputs**：`[0] CLIP`
- **widgets_values**：`[stop_at_clip_layer_int]`（通常为 -1 或 -2）

### EmptyLatentImage
- **职责**：生成指定尺寸的空白 latent
- **inputs**：无
- **outputs**：`[0] LATENT`
- **widgets_values**：`[width_int, height_int, batch_size_int]`

### KSampler
- **职责**：标准 K-Sampler 采样器
- **inputs**：`[0] model (MODEL)`, `[1] positive (CONDITIONING)`, `[2] negative (CONDITIONING)`, `[3] latent_image (LATENT)`
- **outputs**：`[0] LATENT`
- **widgets_values**：`[seed_int, "fixed"|"randomize"|"increment", steps_int, cfg_float, sampler_name_string, scheduler_string, denoise_float]`
- **常用 sampler_name**：`euler`, `euler_ancestral`, `dpmpp_2m`, `dpmpp_2m_sde`, `ddim`
- **常用 scheduler**：`normal`, `karras`, `exponential`, `sgm_uniform`, `simple`

### VAEDecode
- **职责**：将 latent 解码为图像
- **inputs**：`[0] samples (LATENT)`, `[1] vae (VAE)`
- **outputs**：`[0] IMAGE`
- **widgets_values**：无

### VAEEncode
- **职责**：将图像编码为 latent（用于 img2img）
- **inputs**：`[0] pixels (IMAGE)`, `[1] vae (VAE)`
- **outputs**：`[0] LATENT`
- **widgets_values**：无

### SaveImage
- **职责**：保存图像到 ComfyUI output 目录
- **inputs**：`[0] images (IMAGE)`
- **outputs**：无
- **widgets_values**：`[filename_prefix_string]`（通常为 "ComfyUI"）

### LoadImage
- **职责**：从 ComfyUI input 目录加载图像
- **inputs**：无
- **outputs**：`[0] IMAGE`, `[1] MASK`
- **widgets_values**：`[image_filename_string, "image"|"mask"]`

### PreviewImage
- **职责**：预览图像（不保存）
- **inputs**：`[0] images (IMAGE)`
- **outputs**：无
- **widgets_values**：无

---

## LoRA 相关节点

### LoraLoader
- **职责**：加载 LoRA 并注入 MODEL + CLIP
- **inputs**：`[0] model (MODEL)`, `[1] clip (CLIP)`
- **outputs**：`[0] MODEL`, `[1] CLIP`
- **widgets_values**：`[lora_filename_string, model_strength_float, clip_strength_float]`
- **注意**：插入在 CheckpointLoaderSimple 和 CLIPTextEncode 之间

### LoraLoaderModelOnly
- **职责**：仅对 MODEL 注入 LoRA（FLUX 常用）
- **inputs**：`[0] model (MODEL)`
- **outputs**：`[0] MODEL`
- **widgets_values**：`[lora_filename_string, model_strength_float]`

---

## 高分辨率放大节点

### LatentUpscale
- **职责**：在 latent 空间上采样（Hires Fix）
- **inputs**：`[0] samples (LATENT)`
- **outputs**：`[0] LATENT`
- **widgets_values**：`["nearest-exact"|"bilinear"|"area"|"bicubic"|"bislerp", width_int, height_int, "disabled"]`

### ImageScale
- **职责**：像素空间放大
- **inputs**：`[0] image (IMAGE)`
- **outputs**：`[0] IMAGE`
- **widgets_values**：`["nearest-exact"|"bilinear"|"area"|"bicubic"|"lanczos", width_int, height_int, "disabled"|"center"]`

### UpscaleModelLoader
- **职责**：加载 ESRGAN/SwinIR 等超分模型
- **inputs**：无
- **outputs**：`[0] UPSCALE_MODEL`
- **widgets_values**：`[upscale_model_filename_string]`

### ImageUpscaleWithModel
- **职责**：用超分模型放大图像
- **inputs**：`[0] upscale_model (UPSCALE_MODEL)`, `[1] image (IMAGE)`
- **outputs**：`[0] IMAGE`
- **widgets_values**：无

---

## ControlNet 节点

### ControlNetLoader
- **职责**：加载 ControlNet 模型
- **inputs**：无
- **outputs**：`[0] CONTROL_NET`
- **widgets_values**：`[controlnet_filename_string]`

### ControlNetApply (ControlNetApplyAdvanced)
- **职责**：将 ControlNet 应用到 conditioning
- **inputs**：`[0] conditioning (CONDITIONING)`, `[1] control_net (CONTROL_NET)`, `[2] image (IMAGE)`
- **outputs**：`[0] CONDITIONING`
- **widgets_values**：`[strength_float]`（0.0–2.0）

---

## FLUX 特有节点

### DualCLIPLoader
- **职责**：加载 FLUX 使用的双 CLIP（T5XXL + CLIP-L）
- **inputs**：无
- **outputs**：`[0] CLIP`
- **widgets_values**：`[clip_name1_string, clip_name2_string, "flux"]`

### UNETLoader
- **职责**：仅加载 UNET（不含 CLIP/VAE，FLUX 分离加载）
- **inputs**：无
- **outputs**：`[0] MODEL`
- **widgets_values**：`[unet_filename_string, "default"|"fp8_e4m3fn"|"fp8_e4m3fn_fast"|"fp8_e5m2"]`

### CLIPTextEncodeFlux (FluxGuidance)
- **职责**：FLUX 专用文本编码（支持 guidance 参数）
- **inputs**：`[0] clip (CLIP)`, `[1] clip (CLIP)`（T5 + CLIP-L）
- **outputs**：`[0] CONDITIONING`
- **widgets_values**：`[clip_l_prompt, t5xxl_prompt, guidance_float]`

### FluxGuidance（独立 guidance 节点）
- **职责**：为 FLUX conditioning 追加 guidance 值
- **inputs**：`[0] conditioning (CONDITIONING)`
- **outputs**：`[0] CONDITIONING`
- **widgets_values**：`[guidance_float]`（通常 3.5）

### ModelSamplingFlux
- **职责**：FLUX 采样参数配置（max_shift / base_shift）
- **inputs**：`[0] model (MODEL)`
- **outputs**：`[0] MODEL`
- **widgets_values**：`[max_shift_float, base_shift_float, width_int, height_int]`

---

## 高级采样器组合（SamplerCustomAdvanced）

适用于 FLUX / SD3.5 的高级采样管线：

### BasicScheduler
- **inputs**：`[0] model (MODEL)`
- **outputs**：`[0] SIGMAS`
- **widgets_values**：`["simple"|"karras"|..., steps_int, denoise_float]`

### KSamplerSelect
- **inputs**：无
- **outputs**：`[0] SAMPLER`
- **widgets_values**：`["euler"|"euler_ancestral"|"dpmpp_2m"|...]`

### RandomNoise / DisableNoise
- **outputs**：`[0] NOISE`
- **widgets_values**：`[seed_int]` 或无

### SamplerCustomAdvanced
- **inputs**：`[0] noise (NOISE)`, `[1] guider (GUIDER)`, `[2] sampler (SAMPLER)`, `[3] sigmas (SIGMAS)`, `[4] latent_image (LATENT)`
- **outputs**：`[0] output (LATENT)`, `[1] denoised_output (LATENT)`
- **widgets_values**：无

### BasicGuider
- **inputs**：`[0] model (MODEL)`, `[1] conditioning (CONDITIONING)`
- **outputs**：`[0] GUIDER`
- **widgets_values**：无

---

## SDXL 专用节点

### CLIPTextEncodeSDXL
- **职责**：SDXL 双文本编码（含尺寸信息）
- **inputs**：`[0] clip (CLIP)`
- **outputs**：`[0] CONDITIONING`
- **widgets_values**：`[width_int, height_int, crop_w_int, crop_h_int, target_w_int, target_h_int, text_g_string, text_l_string]`

---

## 图像工具节点

### ImageBatch
- **inputs**：`[0] image1 (IMAGE)`, `[1] image2 (IMAGE)`
- **outputs**：`[0] IMAGE`

### ImageCrop
- **widgets_values**：`[width_int, height_int, x_int, y_int]`

### CR Image Pipe In / Out（ComfyUI-Manager 扩展）
- 常用于复杂管线的图像传递

---

## 节点 mode 值说明

| mode 值 | 含义 |
|---------|------|
| 0 | 正常激活 |
| 2 | 静音（Mute）— 跳过执行 |
| 4 | 绕过（Bypass）— 直通输出 |

---

## ComfyUI 自定义节点包（常用）

| 包名 | 提供的节点 | 安装方式 |
|------|-----------|----------|
| ComfyUI-Manager | 节点管理器本身 | GitHub |
| ComfyUI_IPAdapter_plus | IPAdapter 系列 | GitHub |
| ComfyUI-Advanced-ControlNet | 高级 ControlNet | GitHub |
| ComfyUI_Comfyroll_CustomNodes | 通用工具节点 | GitHub |
| comfyui_controlnet_aux | 预处理器（Canny/Depth/Pose） | GitHub |
| ComfyUI-GGUF | GGUF 格式 FLUX 加载 | GitHub |
| x-flux-comfyui | FLUX 专用节点 | GitHub |
