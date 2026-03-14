---
name: frontend-slides
description: Create zero-dependency, animation-rich single-file HTML presentations from scratch or by converting PowerPoint. Use when the user wants to build a presentation, convert PPT/PPTX to web, or create slides for a talk/pitch. Uses "show don't tell" style discovery via visual previews.
---

# Frontend Slides

## Overview

Produce single-file HTML presentations with inline CSS/JS: no npm, no build. Support three modes — new presentation, PPT conversion, or enhance existing HTML. Style is chosen by generating 3 visual previews (show don't tell); every slide must fit the viewport (100vh, no in-slide scroll).

## Core Principles

- **Zero Dependencies** — One HTML file, inline CSS/JS.
- **Show, Don't Tell** — Generate style previews; user picks by seeing.
- **Distinctive Design** — Avoid generic AI aesthetics; use curated presets and typography/color/motion.
- **Viewport Fitting (NON-NEGOTIABLE)** — Each `.slide`: `height: 100vh; height: 100dvh; overflow: hidden;`. Fonts and spacing use `clamp()`. No scrolling inside a slide; split content into more slides if needed.

## Workflow

### Phase 0: Detect Mode

- **Mode A: New** — Create from scratch → Phase 1.
- **Mode B: PPT Conversion** — Convert .pptx → extract content, confirm, style selection, generate HTML (Phase 4).
- **Mode C: Enhancement** — Improve existing HTML; follow density limits and viewport rules when adding content.

### Phase 1: Content Discovery (New)

- Ask in one shot: purpose (pitch/teaching/talk/internal), length (short/medium/long), content readiness, and whether inline editing in browser is needed.
- If images provided: scan, evaluate each (usable or not, concept, colors), co-design outline, confirm with user.

### Phase 2: Style Discovery

- Ask: "Show me options" (recommended) or "I know what I want" (preset list).
- If options: ask vibe (Impressed/Excited/Calm/Inspired, max 2), then generate 3 single-slide HTML previews; user picks A/B/C or mix.
- Use STYLE_PRESETS for presets; save previews under `.claude-design/slide-previews/`.

### Phase 3: Generate Presentation

- Single self-contained HTML; include full viewport-base.css in `<style>`; use Fontshare/Google Fonts; section comments; respect content density per slide type (title, content, feature grid, code, quote, image).

### Phase 4: PPT Conversion

- Run extract script: `python scripts/extract-pptx.py <input.pptx> <output_dir>` (install dependency: `pip install python-pptx`). Confirm extracted slides with user, then Phase 2 style selection, then generate HTML preserving text, images, order, speaker notes.

### Phase 5: Delivery

- Clean preview folder; open HTML in browser; summarize file location, style, slide count, navigation (arrows, space, dots), how to customize (`:root`, fonts, `.reveal`), and if applicable inline edit (hover top-left or E, edit text, Ctrl+S).

## Output Contract

On completion, provide:

- File path, style name, slide count
- Navigation: arrow keys, Space, scroll/swipe, nav dots
- Customization: `:root` variables, font link, `.reveal` for animations
- If inline editing enabled: how to enter edit mode, edit text, save (Ctrl+S)

## Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| STYLE_PRESETS.md | skill root | Curated presets (colors, fonts, signature elements) |
| viewport-base.css | skill root | Mandatory responsive CSS — include in full in every presentation |
| html-template.md | skill root | HTML structure, JS features, code standards |
| animation-patterns.md | skill root | Animation snippets and feeling-to-effect guide |
| scripts/extract-pptx.py | `scripts/` | PPT content extraction (Phase 4); requires `pip install python-pptx` |

**Path conventions by runtime:**
- **Codex (this file):** supporting files are siblings of this `SKILL.md`; script at `scripts/extract-pptx.py` relative to skill root.
- **Claude mirror:** all supporting files live under `.claude/skills/frontend-slides/`; script at `.claude/skills/frontend-slides/scripts/extract-pptx.py`.
- **Gemini mirror:** same layout as Codex; script at `scripts/extract-pptx.py` relative to skill root.
