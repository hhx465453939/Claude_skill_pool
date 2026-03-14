---
description: 从零创建或从 PPT 转制动画丰富的单文件 HTML 演示稿，支持视觉风格预览与零依赖交付
---

# /frontend-slides — 前端幻灯片

你正在使用 **Frontend Slides** 技能：创建零依赖、动画丰富的单文件 HTML 演示，或从 PowerPoint 转制为网页幻灯片。

---

## 使用场景

- **新建演示**：从零做 Pitch、教学、大会演讲、内部汇报用的网页幻灯片
- **PPT 转制**：将 `.pptx` 转为单文件 HTML，保留文字、图片与讲稿
- **增强已有**：在现有 HTML 演示上增删内容或改版，并保证视口适配

---

## 模式与入口

1. **Mode A — 新建**：按 Phase 1 收集用途、页数、内容与是否需「浏览器内可编辑」
2. **Mode B — PPT 转制**：用 `extract-pptx.py` 抽取内容 → 确认 → 选风格 → 生成 HTML
3. **Mode C — 增强**：先读懂现有 HTML，再按「单页内容密度上限」与视口规则做修改

执行前先读本技能完整流程：`.claude/skills/frontend-slides/SKILL.md`。

---

## 不可妥协的规则

- **视口适配**：每页 `.slide` 必须 `height: 100vh; height: 100dvh; overflow: hidden;`，字号与间距用 `clamp()`，禁止单页内滚动
- **内容密度**：单页不超过 SKILL 中规定的标题+要点/段落/卡片/代码行数；超了必须拆成多页
- **风格**：用 STYLE_PRESETS 与「展示 3 个预览再选」的方式，避免通用 AI 审美；每份演示需包含完整 `viewport-base.css`

---

## 标准输出

交付时说明：

- 文件路径、风格名、页数
- 操作方式：方向键 / 空格 / 点击导航点
- 若开启内联编辑：如何进入编辑模式、保存与导出

只有在用户拿到可本地打开的单文件 HTML、且所有适用规则已满足时，才算本次 `/frontend-slides` 完成。
